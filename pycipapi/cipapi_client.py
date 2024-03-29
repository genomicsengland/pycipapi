from pycipapi.models import (
    CipApiOverview,
    CipApiCase,
    ClinicalReport,
    VariantInterpretationLog,
    Referral,
    RequestStatus,
    InterpretationFlag,
    Participant,
    ParticipantConsent,
    ParticipantInterpretedGenome,
    ParticipantClinicalReport,
)
from pycipapi.rest_client import RestClient, returns_item


class CipApiClient(RestClient):

    ENDPOINT_BASE = "api/2"
    AUTH_ENDPOINT = "{url_base}/get-token/".format(url_base=ENDPOINT_BASE)
    IR_ENDPOINT = "{url_base}/interpretation-request".format(url_base=ENDPOINT_BASE)
    EQ_ENDPOINT = "{url_base}/exit-questionnaire".format(url_base=ENDPOINT_BASE)
    CR_ENDPOINT = "{url_base}/clinical-report".format(url_base=ENDPOINT_BASE)
    IG_ENDPOINT = "{url_base}/interpreted-genome".format(url_base=ENDPOINT_BASE)
    REFERRAL_ENDPOINT = "{url_base}/referral".format(url_base=ENDPOINT_BASE)
    FILE_ENDPOINT = "{url_base}/file".format(url_base=ENDPOINT_BASE)
    PARTICIPANTS_ENDPOINT = "{url_base}/participants".format(url_base=ENDPOINT_BASE)
    PAGE_SIZE_MAX = 500

    def __init__(self, url_base, token=None, user=None, password=None, retries=5, fixed_paramters=None):
        """
        If user and password are not provided there will be no token renewal
        :param url_base:
        :param token:
        :param user:
        :param password:
        """
        RestClient.__init__(self, url_base=url_base, retries=retries, fixed_params=fixed_paramters)
        self.token = "JWT {}".format(token) if token is not None else None
        self.user = user
        self.password = password if password else ""
        if (self.token is None) and (self.user is None or self.password is None):
            raise ValueError("Authentication is required. Provide either token or user and password.")
        self.set_authenticated_header()

    def get_token(self):
        url = self.build_url(self.url_base, self.AUTH_ENDPOINT)
        token = self.post(url, payload={
            'username': self.user,
            'password': self.password
        }).get('token')
        return "JWT {}".format(token)

    def get_paginated(self, url, **params):
        query_params, url = self._clean_url(params, url)
        next = True
        while next is not None:
            results = self.get(url=url, params=query_params)
            next = results.get('next')
            if next is not None:
                query_params, url = self._clean_url(parameters=query_params, url=next)
            for r in results.get('results', []):
                yield r

    def get_cases_raw(self, **params):
        """
        gets the un-cast contents of the interpretation request list endpoint
        do not perform migrations
        :type params: dict
        :type page: int
        :type page_size: int
        :type minimize: str
        :rtype: collections.Iterable[dict]
        does not check and exclude on the basis of last_status, unlike get_cases
        :return:
        """
        url = self.build_url(self.url_base, self.IR_ENDPOINT)
        for r in self.get_paginated(url, **params):
            yield r

    def get_case_raw(self, case_id, case_version, **params):
        """
        :type case_id: str
        :type case_version: str
        :rtype: dict
        """

        url = self.build_url(self.url_base, self.IR_ENDPOINT, case_id, case_version) + '/'
        return self.get(url, params=params)

    def register_case_raw(self, payload, **params):
        url = self.build_url(self.url_base, self.IR_ENDPOINT) + '/'
        return self.post(url, payload=payload, params=params)

    def create_referral_raw(self, payload, **params):
        url = self.build_url(self.url_base, self.REFERRAL_ENDPOINT) + '/'
        return self.post(url, payload=payload, params=params)

    def file_upload_raw(self, file_path, user, partner_id, report_id, file_type, **params):
        url = self.build_url(self.url_base, self.FILE_ENDPOINT, partner_id, report_id, file_type) + '/'
        files = {'file': open(file_path, 'rb')}
        data = {'user': user}
        return self.post(url, payload=data, files=files, params=params)

    def change_priority_raw(self, case_id, case_version, priority, **params):
        url = self.build_url(self.url_base, self.IR_ENDPOINT, 'case-priority', case_id, case_version) + '/'
        return self.patch(url, {"case_priority": priority}, params=params)

    def patch_case_raw(self, case_id, case_version, payload, **params):
        url = self.build_url(self.url_base, self.IR_ENDPOINT, case_id, case_version) + '/'
        return self.patch(url, payload=payload, params=params)

    def submit_interpretation_request_raw(self, case_id, case_version, interpretation_request_dict, extra_fields,
                                          **params):
        payload = {"interpretation_request_data": {"json_request": interpretation_request_dict}}
        payload.update(extra_fields)
        return self.patch_case_raw(case_id, case_version, payload, **params)

    def dispatch_raw(self, case_id, case_version, **params):
        url = self.build_url(self.url_base, self.IR_ENDPOINT, 'dispatch', case_id, case_version) + '/'
        return self.put(url, payload=None, params=params)

    def submit_interpreted_genome_raw(self, payload, partner_id, analysis_type, report_id, **params):
        url = self.build_url(self.url_base, self.IG_ENDPOINT, partner_id, analysis_type, report_id) + '/'
        return self.post(url, payload=payload, params=params)

    def submit_clinical_report_raw(self, payload, partner_id, analysis_type, report_id, **params):
        url = self.build_url(self.url_base, self.CR_ENDPOINT, partner_id, analysis_type, report_id) + '/'
        return self.post(url, payload, params=params)

    def submit_variant_interpretation_logs_raw(self, payload, case_id, case_version, **params):
        case_id_version = "{ir_id}-{ir_version}".format(
            ir_id=case_id,
            ir_version=case_version
        )
        url = self.build_url(self.url_base, self.IR_ENDPOINT, case_id_version, 'variant-interpretation-log') + '/'
        return self.post(url, payload, params=params)

    def submit_interpretation_flags_raw(self, payload, case_id, case_version, **params):
        url = self.build_url(self.url_base, self.IR_ENDPOINT, case_id, case_version, 'interpretation-flags') + '/'
        return self.post(url, payload, params=params)

    def get_interpretation_flags_raw(self, case_id, case_version, **params):
        url = self.build_url(self.url_base, self.IR_ENDPOINT, case_id, case_version, 'interpretation-flags') + '/'
        for r in self.get_paginated(url, params=params):
            yield r

    def list_clinical_reports_raw(self, **params):
        """

        :rtype: collections.Iterable[dict]
        """
        url = self.build_url(self.url_base, self.CR_ENDPOINT)
        for r in self.get_paginated(url, params=params):
            yield r

    def list_referral_raw(self, **params):
        """

        :rtype: collections.Iterable[dict]
        """
        url = self.build_url(self.url_base, self.REFERRAL_ENDPOINT)
        for r in self.get_paginated(url, params=params):
            yield r

    def submit_interpretation_flags(self, payload, case_id, case_version, **params):
        """

        :rtype: collections.Iterable[InterpretationFlag]
        """
        flags = self.submit_interpretation_flags_raw(payload, case_id, case_version, **params)
        for flag in flags:
            yield InterpretationFlag(**flag)

    def post_participant_interpreted_genome_raw(self, payload, participant_id, interpretation_service_name = 'genomics_england_additional_findings', **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'interpreted-genome') + '/'
        payload_json =  {
                          "interpreted_genome_data": payload,
                          "interpretation_service_name": interpretation_service_name
                        }
        return self.post(url, payload_json, params=params)

    def post_participant_clinical_report_raw(self, payload, participant_id, interpretation_service_name, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'summary-of-findings', 'interpretation-service', interpretation_service_name) + '/'
        return self.post(url, payload, params=params)

    def get_participant_consent_raw(self, participant_id, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'consent')
        return self.get(url, params=params)

    def post_participant_consent_raw(self, payload, participant_id, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'consent') + '/'
        return self.post(url, payload, params=params)

    def put_participant_consent_raw(self, payload, participant_id, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'consent') + '/'
        return self.put(url, payload, params=params)

    def get_participant_interpreted_genome_raw(self, participant_id, interpretation_service_name, version, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'interpreted-genome', interpretation_service_name, version) + '/'
        return self.get(url, params=params)

    def get_participant_clinical_report_raw(self, participant_id, version, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'summary-of-findings', version) + '/'
        return self.get(url, params=params)

    def list_participants_raw(self, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT) + '/'
        for r in self.get_paginated(url, **params):
            yield r

    def list_participant_interpreted_genomes_raw(self, participant_id, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'interpreted-genome') + '/'
        for r in self.get_paginated(url, params=params):
            yield r

    def list_participant_clinical_reports_raw(self, participant_id, **params):
        url = self.build_url(self.url_base, self.PARTICIPANTS_ENDPOINT, participant_id, 'summary-of-findings') + '/'
        for r in self.get_paginated(url, params=params):
            yield r

    @returns_item(ParticipantConsent)
    def get_participant_consent(self, participant_id, **params):
        """
        :type participant_id: str
        :rtype: ParticipantConsent
        """
        return self.get_participant_consent_raw(participant_id, **params)

    @returns_item(ParticipantClinicalReport)
    def get_participant_clinical_report(self, participant_id, version, **params):
        """
        :type participant_id: str
        :rtype: ParticipantClinicalReport
        """
        return self.get_participant_clinical_report_raw(participant_id, version, **params)

    @returns_item(ParticipantClinicalReport)
    def post_participant_clinical_report(self, payload, participant_id,interpretation_service_name, **params):
        """
        :type participant_id: str
        :rtype: ParticipantClinicalReport
        """
        return self.post_participant_clinical_report_raw(payload, participant_id, interpretation_service_name, **params)

    @returns_item(ParticipantClinicalReport, multi=True)
    def list_participant_clinical_reports(self, participant_id, **params):
        """

        :rtype: collections.Iterable[ParticipantClinicalReport]
        """
        return self.list_participant_clinical_reports_raw(participant_id, **params)

    @returns_item(ParticipantConsent)
    def post_participant_consent(self, payload, participant_id, **params):
        """
        :type participant_id: str
        :rtype: ParticipantConsent
        """
        return self.post_participant_consent_raw(payload, participant_id, **params)

    @returns_item(ParticipantConsent)
    def put_participant_consent(self, payload, participant_id, **params):
        """
        :type participant_id: str
        :rtype: ParticipantConsent
        """
        return self.put_participant_consent_raw(payload, participant_id, **params)

    @returns_item(ParticipantInterpretedGenome)
    def post_participant_interpreted_genome(self, payload, participant_id, **params):
        """
        :type participant_id: str
        :rtype: ParticipantInterpretedGenome
        """
        return self.post_participant_interpreted_genome_raw(payload, participant_id, **params)

    @returns_item(ParticipantInterpretedGenome)
    def get_participant_interpreted_genome(self, participant_id, interpretation_service_name, version, **params):
        """
        :type participant_id: str
        :rtype: ParticipantInterpretedGenome
        """
        return self.get_participant_interpreted_genome_raw(participant_id, interpretation_service_name, version, **params)

    @returns_item(ParticipantInterpretedGenome, multi=True)
    def list_participant_interpreted_genomes(self, participant_id, **params):
        """

        :rtype: collections.Iterable[ParticipantInterpretedGenome]
        """
        return self.list_participant_interpreted_genomes_raw(participant_id, **params)

    @returns_item(InterpretationFlag, multi=True)
    def get_interpretation_flags(self, payload, case_id, case_version, **params):
        """

        :rtype: collections.Iterable[InterpretationFlag]
        """
        return self.get_interpretation_flags_raw(case_id, case_version, **params)

    @returns_item(CipApiOverview, multi=True)
    def get_cases(self, **params):
        """

        :rtype: collections.Iterable[CipApiOverview]
        """
        return self.get_cases_raw(**params)

    @returns_item(CipApiOverview, multi=True)
    def list_cases(self, **params):
        """

        :rtype: collections.Iterable[CipApiOverview]
        """
        return self.get_cases_raw(**params)

    @returns_item(CipApiCase, multi=False)
    def get_case(self, case_id, case_version, **params):
        """
        :type case_id: str
        :type case_version: str
        :rtype: CipApiCase
        """
        return self.get_case_raw(case_id=case_id, case_version=case_version, **params)

    @returns_item(CipApiCase, multi=False)
    def register_case(self, payload, **params):
        """

        :rtype: CipApiCase
        """
        return self.register_case_raw(payload, **params)

    @returns_item(CipApiCase, multi=False)
    def patch_case(self, case_id, case_version, payload, **params):
        return self.patch_case_raw(case_id, case_version, payload, **params)

    @returns_item(CipApiCase, multi=False)
    def submit_interpretation_request(self, case_id, case_version, interpretation_request_dict, extra_fields, **params):
        return self.submit_interpretation_request_raw(case_id, case_version, interpretation_request_dict,
                                                      extra_fields=extra_fields, **params)

    @returns_item(CipApiCase, multi=False)
    def dispatch(self, case_id, case_version, **params):
        return self.dispatch_raw(case_id, case_version, **params)

    @returns_item(CipApiCase, multi=False)
    def change_priority(self, case_id, case_version, priority, **params):
        return self.change_priority_raw(case_id, case_version, priority, **params)

    @returns_item(RequestStatus, multi=False)
    def submit_interpreted_genome(self, payload, partner_id, analysis_type, report_id, **params):
        return self.submit_interpreted_genome_raw(payload, partner_id, analysis_type, report_id, **params)

    @returns_item(Participant, multi=True)
    def list_participants(self, **params):
        """
        This method lists all the participants registered in cipapi, filtered by given params.

        :param params:
        :return: Participant
        """
        return self.list_participants_raw(**params)

    @returns_item(ClinicalReport, multi=True)
    def list_clinical_reports(self, **params):
        """

        :rtype: collections.Iterable[ClinicalReport]
        """
        return self.list_clinical_reports_raw(**params)

    @returns_item(ClinicalReport, multi=False)
    def submit_clinical_report(self, payload, partner_id, analysis_type, report_id, **params):
        """

        :rtype: ClinicalReport
        """
        return self.submit_clinical_report_raw(payload, partner_id, analysis_type, report_id, **params)

    @returns_item(VariantInterpretationLog, multi=False)
    def submit_variant_interpretation_logs(self, vils, case_id, case_version, **params):
        """
        :type vils: list
        :type case_id: int
        :type case_version: int
        :rtype: VariantInterpretationLog
        """
        payload = {"log_entry": vils}
        return self.submit_variant_interpretation_logs_raw(payload, case_id, case_version, **params)

    @returns_item(Referral, multi=True)
    def list_referral(self, **params):
        """

        :rtype: collections.Iterable[Referral]
        """
        return self.list_referral_raw(**params)

    @returns_item(Referral, multi=False)
    def create_referral(self, payload, **params):
        """

        :rtype: Referral
        """
        return self.create_referral_raw(payload, **params)
