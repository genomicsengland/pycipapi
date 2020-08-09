import logging

from protocols.protocol_7_2.reports import Assembly, Program, InterpretationRequestRD, CancerInterpretationRequest, \
    InterpretedGenome as InterpretedGenomeGelModel
from protocols.protocol_7_3.participant import Referral as ReferralGelModel


class PreviousData(Exception):
    pass


class WorkspacePermissions(object):
    def __init__(self, **kwargs):
        self.short_name = kwargs.get('short_name')
        self.long_name = kwargs.get('long_name')
        self.gmc_name = kwargs.get('gmc_name')
        self.groups = kwargs.get('groups')


class InterpretedGenome(object):
    def __init__(self, **kwargs):
        self.status = kwargs.get('status')
        self.gel_qc_outcome = kwargs.get('gel_qc_outcome')
        self.created_at = kwargs.get('created_at')
        self.cip_version = kwargs.get('cip_version')
        self.created_at = kwargs.get('created_at')
        self.interpreted_genome_data = kwargs.get('interpreted_genome_data')
        self.gel_qc_outcome = kwargs.get('gel_qc_outcome')
        self.status = kwargs.get('status')
        self.cva_variants_status = kwargs.get('cva_variants_status')
        self.cva_variants_transaction_id = kwargs.get('cva_variants_transaction_id')

    def __lt__(self, other):
        """

        :type other: InterpretedGenome
        """
        if self.created_at < other.created_at:
            return True
        return False

    @property
    def interpretation_request_payload(self):
        if self.interpreted_genome_data:
            return InterpretedGenomeGelModel.fromJsonDict(self.interpreted_genome_data)


class ReferralTest(object):
    def __init__(self, **kwargs):
        self.referral_test_id = kwargs.get("referral_test_id")
        self.clinical_indication_test_type_id = kwargs.get("clinical_indication_test_type_id")
        self.clinical_indication_test_code = kwargs.get("clinical_indication_test_code")
        self.clinical_indication_test_name = kwargs.get("clinical_indication_test_name")
        self.test_technology_id = kwargs.get("test_technology_id")
        self.testTechnologyDescription = kwargs.get("testTechnologyDescription")
        self.ordering_date = kwargs.get("ordering_date")
        self.interpretation_request = kwargs.get("interpretation_request")
        self.create_at = kwargs.get("create_at")
        self.last_modified = kwargs.get("last_modified")
        self.interpreter_organisation_id = kwargs.get("interpreter_organisation_id")
        self.interpreter_organisation_code = kwargs.get("interpreter_organisation_code")
        self.interpreter_organisation_name = kwargs.get("interpreter_organisation_name")
        self.interpreter_organisation_national_grouping_id = kwargs.get("interpreter_organisation_national_grouping_id")
        self.interpreter_organisation_national_grouping_name = kwargs.get("interpreter_organisation_national_grouping_name")
        self.interpretation_request_id = kwargs.get("interpretation_request_id")
        self.interpretation_request_version = kwargs.get("interpretation_request_version")
    
    def get_interpretation_request_ids(self):
        return self.interpretation_request_id, self.interpretation_request_version

    def get_interpretation_request(self, cip_api_client, **params):
        """

        :type cip_api_client: CipApiClient
        :rtype : CipApiCase
        """
        return cip_api_client.get_case(self.interpretation_request_id, self.interpretation_request_version, **params)


class Referral(object):
    def __init__(self, **kwargs):
        self.referral_id = kwargs.get("referral_id")
        self.referral_uid = kwargs.get("referral_uid")
        self.ordering_date = kwargs.get("ordering_date")
        self.analysis_scope = kwargs.get("analysis_scope")
        self._referral_payload_json = kwargs.get("referral_data")
        self.last_modified = kwargs.get("last_modified")
        self.create_at = kwargs.get("create_at")
        self.requester_organisation_id = kwargs.get("requester_organisation_id")
        self.requester_organisation_code = kwargs.get("requester_organisation_code")
        self.requester_organisation_name = kwargs.get("requester_organisation_name")
        self.requester_organisation_national_grouping_id = kwargs.get("requester_organisation_national_grouping_id")
        self.requester_organisation_national_grouping_name = kwargs.get("requester_organisation_national_grouping_name")
        self.referral_test = [rt for rt in self.process_referral_tests(kwargs.get('referral_test'))]

    @property
    def referral_data(self):
        """

        :rtype: ReferralGelModel
        """
        if not ReferralGelModel.validate(self._referral_payload_json):
            logging.warning('The referral payload is not valid according to the version of GelModels you are using, '
                            'it may raise errors during the serialisation')
        referral_payload = ReferralGelModel.fromJsonDict(self._referral_payload_json)

        return referral_payload

    def process_referral_tests(self, referral_test_data):
        for referral_test in referral_test_data:
            yield ReferralTest(**referral_test)

    def get_interpretation_requests_ids(self):
        for rt in self.referral_test:
            yield rt.get_interpretation_request_ids()
    
    def get_interpretation_requests(self, cip_api_client, **params):
        for rt in self.referral_test:
            yield rt.get_interpretation_request(cip_api_client, **params)


class ClinicalReport(object):
    def __init__(self, **kwargs):
        self.clinical_report_data = kwargs.get('clinical_report_data')
        self.created_at = kwargs.get('created_at')
        self.exit_questionnaire = ExitQuestionnaire(**kwargs.get('exit_questionnaire')) if\
            kwargs.get('exit_questionnaire') else None
        self.clinical_report_version = kwargs.get('clinical_report_version')
        self.valid = kwargs.get('valid')
        self.cva_variants_status = kwargs.get('cva_variants_status')
        self.cva_variants_transaction_id = kwargs.get('cva_variants_transaction_id')
        self.timestamp = kwargs.get('timestamp')


class ExitQuestionnaire(object):
    def __init__(self, **kwargs):
        self.created_at = kwargs.get('created_at')
        self.exit_questionnaire_data = kwargs.get('exit_questionnaire_data')
        self.user = kwargs.get('user')
        self.cva_status = kwargs.get('cva_status')
        self.cva_transaction_id = kwargs.get('cva_transaction_id')


class RequestStatus(object):
    def __init__(self, **kwargs):
        self.created_at = kwargs.get('created_at')
        self.user = kwargs.get('user')
        self.status = kwargs.get('status')

    def is_blocked(self):
        if self.status == 'blocked':
            return True
        return False


class InterpretationFlag(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get('flag').get('name')
        self.description = kwargs.get('flag').get('description')

    def __eq__(self, other):
        if self.name == other.name:
            return True
        return False

    def __hash__(self):
        return hash(self.name)


class CipApiCase(object):
    _map_sample_type2program = {
        'raredisease': Program.rare_disease,
        'cancer': Program.cancer
    }

    def __init__(self, **kwargs):
        self._load_data(**kwargs)

    def _load_data(self, **kwargs):
        self.last_status = kwargs.get('last_status')
        self.created_at = kwargs.get('created_at')
        self.last_modified = kwargs.get('last_modified')
        self.cip = kwargs.get('cip')
        self.group_id = kwargs.get('group_id')
        self.cohort_id = kwargs.get('cohort_id')
        self.sample_type = kwargs.get('sample_type')
        self.interpretation_request_id = kwargs.get('interpretation_request_id')
        self.case_members = kwargs.get('case_members')
        self.version = kwargs.get('version')
        self.gel_tiering_qc_outcome = kwargs.get('gel_tiering_qc_outcome')
        self.labkey_links = kwargs.get('labkey_links')
        self.case_priority = kwargs.get('case_priority')
        self.tags = kwargs.get('tags')
        self.paid = kwargs.get('paid')
        self.family_id = kwargs.get('family_id')
        self.cancer_participant_id = kwargs.get('cancer_participant')
        self.assembly = kwargs.get('assembly')
        self.case_id = kwargs.get('case_id')
        self.number_of_samples = kwargs.get('number_of_samples')
        self.proband = kwargs.get('proband')
        self.referral = Referral(**kwargs.get('referral')) if kwargs.get('referral') else None
        self.interpretation_flags = [InterpretationFlag(**flag) for flag in kwargs.get(
            'interpretation_flag')] if kwargs.get('interpretation_flag') else []
        self.status = [RequestStatus(**s) for s in kwargs.get('status', [])]
        self.files = kwargs.get('files')
        self.interpretation_request_data = kwargs.get('interpretation_request_data')
        self.interpreted_genome = [InterpretedGenome(**ig) for ig in kwargs.get('interpreted_genome', [])]
        self.clinical_report = [ClinicalReport(**cr) for cr in kwargs.get('clinical_report', [])]
        self.workspaces = kwargs.get('workspaces')

    @property
    def interpretation_request_payload(self):
        if self.interpretation_request_data and self.sample_type == 'raredisease':
            return InterpretationRequestRD.fromJsonDict(self.interpretation_request_data['json_request'])
        if self.interpretation_request_data and self.sample_type == 'cancer':
            return CancerInterpretationRequest.fromJsonDict(self.interpretation_request_data['json_request'])

    @property
    def pedigree(self):
        if self.interpretation_request_data and self.sample_type == 'raredisease':
            return self.interpretation_request_payload.pedigree
        return None

    @property
    def cancer_participant(self):
        if self.interpretation_request_data and self.sample_type == 'cancer':
            return self.interpretation_request_payload.cancerParticipant

    @property
    def samples(self):
        if self.interpretation_request_data and self.sample_type == 'raredisease':
            return [sample.SampleId for member in self.pedigree.members for sample in member.samples if member.samples]
        elif self.interpretation_request_data and self.sample_type == 'cancer':
            samples = []
            for m in self.interpretation_request_data.cancerParticipant.matchedSamples:
                samples.append(m.germlineSampleId)
                samples.append(m.tumourSampleId)
            return samples
        return None

    @property
    def is_blocked(self):
        """
        :rtype: bool
        """
        if self.last_status == 'blocked':
            return True
        return False

    @property
    def has_been_ever_blocked(self):
        """
        :rtype: bool
        """
        if True in [s.is_blocked() for s in self.status]:
            return True
        return False

    @property
    def has_been_interpreted(self):
        """
        :rtype: bool
        """
        if self.interpreted_genome:
            return True
        return False

    @property
    def has_clinical_reports(self):
        """
        :rtype: bool
        """
        if self.clinical_report:
            return True
        return False

    @property
    def program(self):
        return self._map_sample_type2program.get(self.sample_type)

    @property
    def number_of_clinical_reports(self):
        return len(self.clinical_report)

    @property
    def has_been_closed(self):
        """
        :rtype: bool
        """
        if True in [s.status == 'report_generated' for s in self.status] or \
                True in [s.status == 'report_sent' for s in self.status]:
            return True
        else:
            return False

    @property
    def has_been_dispatch(self):
        """
        :rtype: bool
        """
        if True in [s.status == 'dispatched' for s in self.status]:
            return True
        else:
            return False

    @property
    def is_closed(self):
        """
        :rtype: bool
        """
        if self.last_status == 'report_sent':
            return True
    @property
    def is_rare_disease(self):
        """
        :rtype: bool
        """
        return self.program == Program.rare_disease

    @property
    def is_cancer(self):
        """
        :rtype: bool
        """
        return self.program == Program.cancer

    @property
    def is_assembly_38(self):
        """
        :rtype: bool
        """
        return self.assembly == Assembly.GRCh38

    @property
    def is_assembly_37(self):
        """
        :rtype: bool
        """
        return self.assembly == Assembly.GRCh37

    def __lt__(self, other):
        """

        :type other: CipApiOverview
        """
        if self.interpretation_request_id < other.interpretation_request_id:
            return True
        elif self.interpretation_request_id == other.interpretation_request_id:
            if self.version < other.version:
                return True
        return False

    def dispatch(self, cip_api_client, **params):
        """

        :type cip_api_client: CipApiClient
        """
        self._load_data(**cip_api_client.dispatch_raw(self.interpretation_request_id, self.version, **params))

    def submit_interpretation_request(self, cip_api_client, payload, extra_fields, force=False, **params):
        """

        :type cip_api_client: CipApiClient
        """
        if not self.interpretation_request_data or force:
            self._load_data(**cip_api_client.submit_interpretation_request_raw(
                case_id=self.interpretation_request_id, case_version=self.version, interpretation_request_dict=payload,
                extra_fields=extra_fields, **params
            ))
        else:
            raise PreviousData('This case has already an interpretation request associate, if you still want to upload'
                               'a new one use `force=True`')

    def patch_case(self, cip_api_client, payload, **params):
        """

        :type cip_api_client: CipApiClient
        """
        self._load_data(**cip_api_client.patch_case_raw(case_id=self.interpretation_request_id,
                                                        case_version=self.version,
                                                        payload=payload, **params
                                                        ))

    def submit_interpreted_genome(self, cip_api_client, payload, partner_id, analysis_type, report_id, **params):
        """

        :type cip_api_client: CipApiClient
        """
        self.interpreted_genome.append(InterpretedGenome(**cip_api_client.submit_interpreted_genome_raw(
            payload=payload, partner_id=partner_id, analysis_type=analysis_type, report_id=report_id, **params
        )))

    def submit_interpretation_flags(self, cip_api_client, payload, **params):
        """

        :type cip_api_client: CipApiClient
        """
        flags = [flag for flag in cip_api_client.submit_interpretation_flags(
            payload, self.interpretation_request_id, self.version, **params)]
        set_of_flags = set(self.interpretation_flags)
        set_of_flags.update(set(flags))
        self.interpretation_flags = list(set_of_flags)

    def submit_clinical_report(self, cip_api_client, payload, partner_id, analysis_type, report_id, **params):
        """

        :type cip_api_client: CipApiClient
        """
        self.clinical_report.append(ClinicalReport(**cip_api_client.submit_clinical_report_raw(
            payload=payload, partner_id=partner_id, analysis_type=analysis_type, report_id=report_id, **params
        )))

    def get_exit_questionnaire(self):
        if self.has_clinical_reports:
            list_of_cr = self.clinical_report
            list_of_cr.reverse()
            for cr in list_of_cr:
                if cr.exit_questionnaire:
                    return cr.exit_questionnaire
        return None

    def get_exit_questionnaires(self):
        if self.has_clinical_reports:
            for cr in self.clinical_report:
                if cr.exit_questionnaire:
                    yield cr.exit_questionnaire


class CipApiOverview(object):
    def __init__(self, **kwargs):
        self._load_data(**kwargs)

    def _load_data(self, **kwargs):
        self.interpretation_request_id = int(kwargs.get('interpretation_request_id', '.-.').split('-')[0])
        self.version = kwargs.get('interpretation_request_id', '.-.').split('-')[1]
        self.cip = kwargs.get('cip')
        self.cohort_id = kwargs.get('cohort_id')
        self.sample_type = kwargs.get('sample_type')
        self.last_status = kwargs.get('last_status')
        self.family_id = kwargs.get('family_id')
        self.cancer_participant_id = kwargs.get('cancer_participant')
        self.proband = kwargs.get('proband')
        self.number_of_samples = kwargs.get('number_of_samples')
        self.last_update = kwargs.get('last_update')
        self.sites = kwargs.get('sites')
        self.case_priority = kwargs.get('case_priority')
        self.tags = kwargs.get('tags')
        self.assembly = kwargs.get('assembly')
        self.last_modified = kwargs.get('last_modified')
        self.clinical_reports = kwargs.get('clinical_reports')
        self.interpreted_genomes = kwargs.get('interpreted_genomes')
        self.files = kwargs.get('files')
        self.workflow_status = kwargs.get('workflow_status')
        self.cva_variants_status = kwargs.get('cva_variants_status')
        self.cva_variants_transaction_id = kwargs.get('cva_variants_transaction_id')
        self.case_id = kwargs.get('case_id')
        self.status = [RequestStatus(**s) for s in kwargs.get('status', [])]
        self.referral = Referral(**kwargs.get('referral')) if kwargs.get('referral') else None

    def get_case(self, cip_api_client, **params):
        """

        :type cip_api_client: CipApiClient
        :rtype : CipApiCase
        """
        return cip_api_client.get_case(self.interpretation_request_id, self.version, **params)

    def __lt__(self, other):
        """

        :type other: CipApiOverview
        """
        if self.interpretation_request_id < other.interpretation_request_id:
            return True
        elif self.interpretation_request_id == other.interpretation_request_id:
            if self.version < other.version:
                return True
        return False

    def __eq__(self, other):
        """

        :type other: CipApiOverview
        """
        if self.interpretation_request_id == other.interpretation_request_id and self.version == other.version:
            return True
        return False


class CasesByGroup(object):
    def __init__(self, cip_api_client, group_id, **params):
        """

        :type cip_api_client: CipApiClient
        :type family: str
        """

        self.cases = [c for c in cip_api_client.get_cases(group_id=group_id, **params)]

    @property
    def is_group_registered(self):
        if self.cases:
            return True
        else:
            return False
    @property
    def last_version(self):
        if not self.is_group_registered:
            return None
        else:
            return sorted(self.cases)[-1]
