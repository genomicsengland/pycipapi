from protocols.cva_1_0_0 import TieredVariantInjectRD, TieredVariantInjectCancer, CandidateVariantInjectRD, \
    CandidateVariantInjectCancer, ReportedVariantInjectRD, ReportedVariantInjectCancer, ExitQuestionnaireInjectRD, \
    ExitQuestionnaireInjectCancer, CancerGermlineVariantLevelQuestionnaire, CancerSomaticVariantLevelQuestionnaire, \
    ReportEventQuestionnaireRD, ReportedVariantQuestionnaireRD, ExitQuestionnaireRD
from protocols.reports_5_0_0 import Program, VariantCoordinates
from pycipapi.cipapi_client import CipApiCase


class CvaHelper(object):
    """
    This class has helper methods to generate CVA injection objects from CIPAPI cases.
    """

    @staticmethod
    def generate_tiered_variant_inject(case):
        """
        Tiered variants injection fields are described here:
        https://cnfl.extge.co.uk/display/IPI/CVA+mapping+data+from+the+CIPAPI+model+to+the+CVA+model
        :type case: CipApiCase
        :rtype: TieredVariantInjectRD or TieredVariantInjectCancer
        """
        interpretation_request = case.get_interpretation_request()
        interpreted_genome = case.get_tiering_interpreted_genome()
        if case.is_rare_disease():
            tiered_variant_inject = TieredVariantInjectRD(
                id=case.case_id,
                version=case.case_version,
                assembly=case.assembly,
                interpretedGenome=interpreted_genome,
                author='tiering',
                authorVersion=interpreted_genome.softwareVersions.get('tiering', None),
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpreted_genome.versionControl.gitVersionControl)
        elif case.is_cancer():
            tiered_variant_inject = TieredVariantInjectCancer(
                id=case.case_id,
                version=case.case_version,
                assembly=case.assembly,
                interpretedGenome=interpreted_genome,
                author='tiering',
                authorVersion=interpreted_genome.softwareVersions.get('tiering', None),
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpreted_genome.versionControl.gitVersionControl)

        return tiered_variant_inject

    @staticmethod
    def generate_candidate_variant_inject(case):
        """
        :type case: CipApiCase
        :rtype: CandidateVariantInjectRD or CandidateVariantInjectCancer
        """
        interpretation_request = case.get_interpretation_request()
        interpreted_genome = case.get_interpreted_genome()
        composed_case_id = "{parent_id}-{parent_version}".format(
            parent_id=case.case_id, parent_version=case.case_version)
        if case.is_rare_disease():
            candidate_variant_inject = CandidateVariantInjectRD(
                id=composed_case_id,
                version=case.interpreted_genome_version,
                parentId=case.case_id,
                parentVersion=case.case_version,
                assembly=case.assembly,
                interpretedGenome=interpreted_genome,
                author=interpreted_genome.interpretationService,
                authorVersion=str(case.interpretation_service_version),
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpreted_genome.versionControl.gitVersionControl)
        elif case.is_cancer():
            candidate_variant_inject = CandidateVariantInjectCancer(
                id=composed_case_id,
                version=case.interpreted_genome_version,
                parentId=case.case_id,
                parentVersion=case.case_version,
                assembly=case.assembly,
                interpretedGenome=interpreted_genome,
                author=interpreted_genome.interpretationService,
                authorVersion=str(case.interpretation_service_version),
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpreted_genome.versionControl.gitVersionControl)

        return candidate_variant_inject

    @staticmethod
    def generate_reported_variant_inject(case):
        """
        :type case: CipApiCase
        :rtype: ReportedVariantInjectRD or ReportedVariantInjectCancer
        """
        interpretation_request = case.get_interpretation_request()
        clinical_report = case.get_clinical_report()
        composed_case_id = "{parent_id}-{parent_version}".format(
            parent_id=case.case_id, parent_version=case.case_version)
        if case.is_rare_disease():
            reported_variant_inject = ReportedVariantInjectRD(
                id=composed_case_id,
                version=case.clinical_report_version,
                parentId=case.case_id,
                parentVersion=case.case_version,
                assembly=case.assembly,
                clinicalReport=clinical_report,
                author=clinical_report.user,
                authorVersion=None,
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpretation_request.versionControl.gitVersionControl)
        elif case.is_cancer():
            reported_variant_inject = ReportedVariantInjectCancer(
                id=composed_case_id,
                version=case.clinical_report_version,
                parentId=case.case_id,
                parentVersion=case.case_version,
                assembly=case.assembly,
                clinicalReport=clinical_report,
                author=clinical_report.user,
                authorVersion=None,
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpretation_request.versionControl.gitVersionControl)

        return reported_variant_inject

    @staticmethod
    def generate_exit_questionnaire_inject(case):
        """
        :type case: CipApiCase
        :rtype: ExitQuestionnaireInjectRD or ExitQuestionnaireInjectCancer
        """
        interpretation_request = case.get_interpretation_request()
        exit_questionnaire = case.get_exit_questionnaire()
        composed_case_id = "{parent_id}-{parent_version}".format(
            parent_id=case.case_id, parent_version=case.case_version)
        if case.is_rare_disease():
            exit_questionnaire_inject = ExitQuestionnaireInjectRD(
                id=composed_case_id,
                version=case.clinical_report_version,
                parentId=case.case_id,
                parentVersion=case.case_version,
                assembly=case.assembly,
                # transform RareDiseaseExitQuestionnaire into ExitQuestionnaireRD
                exitQuestionnaireRd=CvaHelper.generate_exit_questionnaire_rd(case),
                author=exit_questionnaire.reporter,
                authorVersion=None,
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpretation_request.versionControl.gitVersionControl)
        elif case.is_cancer():
            exit_questionnaire_inject = ExitQuestionnaireInjectCancer(
                id=composed_case_id,
                version=case.clinical_report_version,
                parentId=case.case_id,
                parentVersion=case.case_version,
                assembly=case.assembly,
                # transform [CancerGermlineVariantLevelQuestions] into [CancerGermlineVariantLevelQuestionnaire]
                cancerGermlineExitQuestionnaires=CvaHelper.extract_cancer_germline_exit_questionnaires(case),
                # transform [CancerSomaticVariantLevelQuestions] into [CancerSomaticVariantLevelQuestionnaire]
                cancerSomaticExitQuestionnaires=CvaHelper.extract_cancer_somatic_exit_questionnaires(case),
                cancercaseLevelQuestions=exit_questionnaire.caseLevelQuestions,
                # TODO: transform array<AdditionalVariantsQuestions> into string
                otherActionableVariants=None,    #exit_questionnaire.otherActionableVariants,
                additionalComments=exit_questionnaire.additionalComments,
                author=exit_questionnaire.reporter,
                authorVersion=None,
                workspace=interpretation_request.workspace,
                groupId=case.group_id,
                cohortId=case.cohort_id,
                reportModelVersion=interpretation_request.versionControl.gitVersionControl)

        return exit_questionnaire_inject

    @staticmethod
    def extract_cancer_germline_exit_questionnaires(case):
        """
        :type case: CipApiCase
        :rtype: list
        """
        assembly = case.assembly
        exit_questionnaire = case.get_exit_questionnaire()

        cancer_germline_exit_questionnaires = []
        if isinstance(exit_questionnaire.germlineVariantLevelQuestions, list):
            for question in exit_questionnaire.germlineVariantLevelQuestions:
                if len(question.variantDetails.split(
                        ":")) != 4:  # The model definition ensures variantDetails is a string
                    raise ValueError(
                        "variantDetails: {variant_details} is not in format chromosome:position:reference:alternate".format(
                            variant_details=question.variantDetails
                        )
                    )
                chromosome, position, reference, alternate = question.variantDetails.split(":")

                variant_coordinates = VariantCoordinates(
                    alternate=alternate,
                    assembly=assembly,
                    chromosome=chromosome,
                    position=int(position),
                    reference=reference)

                cancer_germline_exit_questionnaire = CancerGermlineVariantLevelQuestionnaire(
                    variantCoordinates=variant_coordinates,
                    variantLevelQuestions=question,
                )
                cancer_germline_exit_questionnaires.append(cancer_germline_exit_questionnaire)
        return cancer_germline_exit_questionnaires

    @staticmethod
    def extract_cancer_somatic_exit_questionnaires(case):
        """
        :type case: CipApiCase
        :rtype: list
        """
        assembly = case.assembly
        exit_questionnaire = case.get_exit_questionnaire()
        cancer_somatic_exit_questionnaires = []
        if isinstance(exit_questionnaire.somaticVariantLevelQuestions, list):
            for question in exit_questionnaire.somaticVariantLevelQuestions:
                if len(question.variantDetails.split(
                        ":")) != 4:  # The model definition ensures variantDetails is a string
                    raise ValueError(
                        "variantDetails: {variant_details} is not in format chromosome:position:reference:alternate".format(
                            variant_details=question.variantDetails
                        )
                    )
                chromosome, position, reference, alternate = question.variantDetails.split(":")

                variant_coordinates = VariantCoordinates(
                    alternate=alternate,
                    assembly=assembly,
                    chromosome=chromosome,
                    position=int(position),
                    reference=reference)

                cancer_somatic_exit_questionnaire = CancerSomaticVariantLevelQuestionnaire(
                    variantCoordinates=variant_coordinates,
                    variantLevelQuestions=question,
                )
                cancer_somatic_exit_questionnaires.append(cancer_somatic_exit_questionnaire)
        return cancer_somatic_exit_questionnaires

    @staticmethod
    def generate_exit_questionnaire_rd(case):
        """

        :type case: CipApiCase
        :rtype: ExitQuestionnaireRD
        """

        assembly = case.assembly
        exit_questionnaire = case.get_exit_questionnaire()

        reported_variant_q_rd_list = []
        for vglq in exit_questionnaire.variantGroupLevelQuestions:
            variant_group = vglq.variantGroup

            for vlq in vglq.variantLevelQuestions:
                report_event_q_rd = ReportEventQuestionnaireRD(
                    groupOfVariants=variant_group,
                    variantLevelQuestions=vlq,
                    variantGroupLevelQuestions=vglq,
                    familyLevelQuestions=exit_questionnaire.familyLevelQuestions,
                )

                if len(vlq.variantDetails.split(":")) == 4:
                    chromosome, position, reference, alternate = vlq.variantDetails.split(":")
                else:
                    raise ValueError(
                        "RD Exit Questionnaire expects variantDetails with format chr:pos:ref:alt "
                        "but received {vd}".format(vd=vlq.variantDetails))

                variant_coordinates = VariantCoordinates(
                    alternate=alternate, assembly=assembly, chromosome=chromosome, position=int(position),
                    reference=reference)

                reported_variant_q_rd = ReportedVariantQuestionnaireRD(
                    variantCoordinates=variant_coordinates,
                    reportEvent=report_event_q_rd,
                )
                reported_variant_q_rd_list.append(reported_variant_q_rd)

        exit_questionnaire_rd = ExitQuestionnaireRD(
            variants=reported_variant_q_rd_list)
        return exit_questionnaire_rd
