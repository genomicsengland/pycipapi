import logging

from protocols.migration.base_migration import MigrationError

from pycipapi.rest_client import RestClient, NotFound, BlockedCase
from protocols.participant_1_0_3 import Pedigree, PedigreeMember
from protocols.reports_5_0_0 import Assembly, InterpretedGenomeRD, ClinicalReportRD, Program, \
    CancerInterpretationRequest, CancerInterpretedGenome, RareDiseaseExitQuestionnaire, CancerExitQuestionnaire, \
    InterpretationRequestRD, ClinicalReportCancer, CancerParticipant
from protocols.migration.migration_helpers import MigrationHelpers


class CipApiClient(RestClient):

    ENDPOINT_BASE = "api/2"
    AUTH_ENDPOINT = "{url_base}/get-token/".format(url_base=ENDPOINT_BASE)
    IR_ENDPOINT = "{url_base}/interpretation-request/{ir_id}/{ir_v}"
    IR_LIST_ENDPOINT = "{url_base}/interpretation-request?page={page}&page_size=100"
    EQ_ENDPOINT = "{url_base}/exit-questionnaire/{ir_id}/{ir_v}/{cr_v}"

    def __init__(self, url_base, token=None, user=None, password=None):
        """
        If user and password are not provided there will be no token renewal
        :param url_base:
        :param token:
        :param user:
        :param password:
        """
        RestClient.__init__(self, url_base)
        self.token = "JWT {}".format(token) if token is not None else None
        self.user = user
        self.password = password
        if (self.token is None) and (self.user is None or self.password is None):
            raise ValueError("Authentication is required. Provide either token or user and password.")
        self.set_authenticated_header()

    def get_token(self):
        token = self.post(self.AUTH_ENDPOINT, payload={
            'username': self.user,
            'password': self.password
        }).get('token')
        return "JWT {}".format(token)

    def get_cases(self, assembly=None, sample_type=None, params={}):
        page = 1
        while True:
            try:
                results = self.get(
                    endpoint=self.IR_LIST_ENDPOINT.format(url_base=self.ENDPOINT_BASE, page=page),
                    url_params=params)["results"]
            except NotFound:
                logging.info("Finished iterating through report events in the CIPAPI")
                break
            for result in results:
                last_status = result["last_status"]
                if last_status in ["blocked", "waiting_payload"]:
                    continue
                if assembly and result['assembly'] != assembly:
                    continue
                if sample_type and result['sample_type'] != sample_type:
                    continue
                case_id, case_version = result["interpretation_request_id"].split("-")
                try:
                    case = self.get_case(case_id, case_version)
                except MigrationError, ex:
                    logging.warning("Case with id {} and version {} failed migration".format(case_id, case_version))
                    continue
                yield case
            page += 1

    def get_case(self, ir_id, ir_version):
        # fetch the interpretation request
        case = None
        try:
            raw_interpretation_request = self.get(
                endpoint=self.IR_ENDPOINT.format(url_base=self.ENDPOINT_BASE, ir_id=ir_id, ir_v=ir_version))
            case = CipApiCase(raw_interpretation_request)
        except NotFound:
            logging.warning("Not found case with id {id} and version {version}".format(id=ir_id, version=ir_version))
        # fetch the exit questionnaire
        try:
            if case and case.raw_clinical_report:
                exit_questionnaire = self.get(
                    endpoint=self.EQ_ENDPOINT.format(
                        url_base=self.ENDPOINT_BASE, ir_id=case.case_id,
                        ir_v=case.case_version, cr_v=case.clinical_report_version))
                case.set_exit_questionnaire(exit_questionnaire)
        except NotFound:
            logging.warning("Not found questionnaire with id {id} and version {version}".format(
                id=case.case_id, version=case.case_version))
        except BlockedCase:
            logging.warning("Blocked case with id {id} and version {version}".format(
                id=case.case_id, version=case.case_version))
        return case


class CipApiCase(object):

    map_sampletype2program = {
        'raredisease': Program.rare_disease,
        'cancer': Program.cancer
    }

    def __init__(self, raw_case):
        self.raw_case = raw_case

        # reads some fields from the raw case
        self.program = self.map_sampletype2program[self.raw_case['sample_type']]
        self.assembly = self.raw_case.get('assembly')
        if self.is_rare_disease():
            self.group_id = self.raw_case.get('family_id')
        elif self.is_cancer():
            self.group_id = self.raw_case.get('cancer_participant')
        self.cohort_id = self.raw_case.get('cohort_id')
        self.raw_interpretation_request, self.case_id, self.case_version = self._get_raw_interpretation_request()

        # creates an interpretation request
        self.interpretation_request = self.get_interpretation_request()

        # creates the interpreted genome with the tiering results
        self.tiering_interpreted_genome = self.get_tiering_interpreted_genome()

        # loads other raw data
        self.raw_interpreted_genome, self.interpreted_genome_version, self.interpretation_service_version = \
            self._get_latest_raw_interpreted_genome()
        self.raw_clinical_report, self.clinical_report_version = self._get_latest_raw_clinical_report()
        if self.is_rare_disease():
            self.raw_pedigree = self._get_raw_pedigree()
        if self.is_cancer():
            self.raw_cancer_participant = self._get_raw_cancer_participant()
        self.raw_questionnaire = None

    def _get_raw_interpretation_request(self):
        """

        :return:
        """
        try:
            data = self.raw_case['interpretation_request_data']['json_request']
            identifier = str(self.raw_case['interpretation_request_id'])
            version = int(self.raw_case['version'])
        except ValueError, ex:
            logging.error("Something is very wrong with this case formatting: {}".format(ex.message))
            raise ex
        return data, identifier, version

    def _get_latest_raw_interpreted_genome(self):
        """

        :return:
        """
        ig_list = self.raw_case.get('interpreted_genome')
        sorted_ig_list = sorted(ig_list, key=lambda ig: ig['created_at'], reverse=True)
        latest_ig = next((ig for ig in sorted_ig_list), None)
        if latest_ig:
            data = latest_ig.get('interpreted_genome_data', None)
            version = latest_ig.get('cip_version', None)
            cip_version = latest_ig.get('cip_version', None)
            return data, int(version) if version else version, int(cip_version) if cip_version else cip_version
        else:
            return None, None, None

    def _get_latest_raw_clinical_report(self):
        """

        :return:
        """
        cr_list = self.raw_case.get('clinical_report')
        sorted_cr_list = sorted(cr_list, key=lambda cr: cr['created_at'], reverse=True)
        latest_cr = next((cr for cr in sorted_cr_list if cr != []), None)
        if latest_cr:
            data = latest_cr.get('clinical_report_data', None) if latest_cr else None
            version = latest_cr.get('clinical_report_version', None) if latest_cr else None
            return data, int(version) if version else version
        else:
            return None, None

    def _get_raw_pedigree(self):
        raw_pedigree = self.raw_case['interpretation_request_data']['json_request']['pedigree']
        return raw_pedigree

    def _get_raw_cancer_participant(self):
        raw_cancer_participant = self.raw_case['interpretation_request_data']['json_request']['cancerParticipant']
        return raw_cancer_participant

    def set_exit_questionnaire(self, questionnaire):
        self.raw_questionnaire = questionnaire['exit_questionnaire_data']

    def get_interpretation_request(self):
        """
        :return:
        :rtype: InterpretationRequestRD or CancerInterpretationRequest
        """
        if self.is_rare_disease():
            interpretation_request = MigrationHelpers.migrate_interpretation_request_rd_to_latest(
                json_dict=self.raw_interpretation_request, assembly=self.assembly)
        elif self.is_cancer():
            interpretation_request = MigrationHelpers.migrate_interpretation_request_cancer_to_latest(
                json_dict=self.raw_interpretation_request, assembly=self.assembly)
        else:
            raise ValueError("Non supported program")
        return interpretation_request

    def get_tiering_interpreted_genome(self):
        """
        :return:
        :rtype: InterpretedGenomeRD or CancerInterpretedGenome
        """
        if self.is_rare_disease():
            interpreted_genome = MigrationHelpers.migrate_interpretation_request_rd_to_interpreted_genome_latest(
                json_dict=self.raw_interpretation_request, assembly=self.assembly)
        elif self.is_cancer():
            interpreted_genome = MigrationHelpers.migrate_interpretation_request_cancer_to_interpreted_genome_latest(
                json_dict=self.raw_interpretation_request, assembly=self.assembly, interpretation_service='tiering',
                reference_database_versions={}, software_versions={}, report_url=None, comments=[])
        else:
            raise ValueError("Non supported program")
        return interpreted_genome

    def has_interpreted_genome(self):
        return self.raw_interpreted_genome is not None

    def get_interpreted_genome(self):
        """
        :return:
        :rtype: InterpretedGenomeRD or CancerInterpretedGenome
        """
        interpreted_genome = None
        if self.has_interpreted_genome():
            if self.is_rare_disease():
                interpreted_genome = MigrationHelpers.migrate_interpretation_request_rd_to_interpreted_genome_latest(
                    json_dict=self.raw_interpreted_genome, assembly=self.assembly,
                    interpretation_request_version=self.case_version)
            elif self.is_cancer():
                cancer_participant = self.get_cancer_participant()
                interpreted_genome = MigrationHelpers.migrate_interpretation_request_cancer_to_interpreted_genome_latest(
                    json_dict=self.raw_interpreted_genome, assembly=self.assembly,
                    participant_id=cancer_participant.individualId,
                    sample_id=cancer_participant.tumourSamples[0].sampleId,
                    interpretation_request_version=self.case_version,
                    interpretation_service="unknown")
            else:
                raise ValueError("Non supported program")
        return interpreted_genome

    def has_clinical_report(self):
        return self.raw_clinical_report is not None

    def get_clinical_report(self):
        """
        :return:
        :rtype: ClinicalReportRD or ClinicalReportCancer
        """
        clinical_report = None
        if self.has_clinical_report():
            if self.is_rare_disease():
                clinical_report = MigrationHelpers.migrate_clinical_report_rd_to_latest(
                    json_dict=self.raw_clinical_report, assembly=self.assembly)
            elif self.is_cancer():
                participant_id = self.interpretation_request.cancerParticipant.individualId
                sample_id = self.interpretation_request.cancerParticipant.tumourSamples[0].sampleId
                clinical_report = MigrationHelpers.migrate_clinical_report_cancer_to_latest(
                    json_dict=self.raw_clinical_report, assembly=self.assembly,
                    sample_id=sample_id, participant_id=participant_id)
            else:
                raise ValueError("Non supported program")
        return clinical_report

    def get_pedigree(self):
        """
        :rtype: Pedigree
        """
        if self.is_rare_disease():
            return MigrationHelpers.migrate_pedigree_to_latest(self.raw_pedigree)
        else:
            raise ValueError("There are no pedigrees for cancer cases")

    @staticmethod
    def get_proband(pedigree):
        """

        :param pedigree:
        :type pedigree: Pedigree
        :rtype: PedigreeMember
        :return:
        """
        proband = None
        for participant in pedigree.members:
            if participant.isProband:
                proband = participant
        return proband

    def get_cancer_participant(self):
        """
        :rtype: CancerParticipant
        """
        if self.is_cancer():
            return MigrationHelpers.migrate_cancer_participant_to_latest(self.raw_cancer_participant)
        else:
            raise ValueError("There are no cancer participants for rare disease cases")

    def has_exit_questionnaire(self):
        return self.raw_questionnaire is not None

    def get_exit_questionnaire(self):
        """
        :return:
        :rtype: RareDiseaseExitQuestionnaire or CancerExitQuestionnaire
        """
        exit_questionnaire = None
        if self.has_exit_questionnaire():
            if self.is_rare_disease():
                exit_questionnaire = MigrationHelpers.migrate_exit_questionnaire_rd_to_latest(
                    json_dict=self.raw_questionnaire)
            elif self.is_cancer():
                exit_questionnaire = CancerExitQuestionnaire.fromJsonDict(jsonDict=self.raw_questionnaire)
            else:
                raise ValueError("Non supported program")
        return exit_questionnaire

    def is_rare_disease(self):
        return self.program == Program.rare_disease

    def is_cancer(self):
        return self.program == Program.cancer

    def is_assembly_38(self):
        return self.assembly == Assembly.GRCh38

    def is_assembly_37(self):
        return self.assembly == Assembly.GRCh37

    @staticmethod
    def get_proband(pedigree):
        """

        :param pedigree:
        :type pedigree: Pedigree
        :rtype: PedigreeMember
        :return:
        """
        proband = None
        for participant in pedigree.members:
            if participant.isProband:
                proband = participant
        return proband

    @staticmethod
    def split_assembly_from_patch(interpretation_request_rd_or_cancer):
        return next((assembly for assembly in interpretation_request_rd_or_cancer.genomeAssemblyVersion.split('.')),
                    None)
