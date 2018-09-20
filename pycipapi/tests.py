import os
import logging
from unittest import TestCase

from protocols.migration.base_migration import MigrationError
from protocols.reports_5_0_0 import Program, ClinicalReportCancer
from protocols.cva_1_0_0 import ReportEventType, Assembly, Variant, TieredVariantInjectRD, TieredVariantInjectCancer, \
    CandidateVariantInjectRD, CandidateVariantInjectCancer, ReportedVariantInjectRD, ReportedVariantInjectCancer, \
    ExitQuestionnaireInjectRD, ExitQuestionnaireInjectCancer
from protocols.reports_5_0_0 import InterpretedGenomeRD, ClinicalReportRD, CancerInterpretationRequest, \
    CancerInterpretedGenome, RareDiseaseExitQuestionnaire, CancerExitQuestionnaire, InterpretationRequestRD
from protocols.participant_1_1_0 import Pedigree

from pycipapi.cipapi_client import CipApiClient, CipApiCase
from pycipapi.cva_helper import CvaInjectionHelper


class TestPyCipApi(TestCase):
    # credentials
    CIPAPI_URL_BASE = os.getenv("CIPAPI_URL")
    GEL_USER = os.getenv("GEL_USER")
    GEL_PASSWORD = os.getenv("GEL_PASSWORD")

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        if self.GEL_PASSWORD is None:
            self.GEL_PASSWORD = ""
        if not self.CIPAPI_URL_BASE or not self.GEL_USER:
            logging.error("Please set the configuration environment variables: CVA_URL, GEL_USER, GEL_PASSWORD")
            raise ValueError("Missing config")
        self.cipapi = CipApiClient(self.CIPAPI_URL_BASE, user=self.GEL_USER, password=self.GEL_PASSWORD)

    def test_get_rare_disease_case(self):

        case_id = "23"
        case_version = 4
        case = self.cipapi.get_case(case_id, case_version)

        # compulsory fields
        ir = case.get_interpretation_request()
        validation = InterpretationRequestRD.validate(ir.toJsonDict(), verbose=True)
        self.assertTrue(validation.result, validation.messages)
        tig = case.get_tiering_interpreted_genome()
        validation = InterpretedGenomeRD.validate(tig.toJsonDict(), verbose=True)
        self.assertTrue(validation.result, validation.messages)
        ped = case.get_pedigree()
        validation = Pedigree.validate(ped.toJsonDict(), verbose=True)
        self.assertTrue(validation.result, validation.messages)

        # injection objects
        tv_inject = CvaInjectionHelper.generate_tiered_variant_inject(case)
        validation = TieredVariantInjectRD.validate(tv_inject.toJsonDict(), verbose=True)
        self.assertTrue(validation.result, validation.messages)

        # optional data
        ig = case.get_interpreted_genome()
        has_ig = False
        if ig:
            self.assertTrue(InterpretedGenomeRD.validate(ig.toJsonDict()))
            cv_inject = CvaInjectionHelper.generate_candidate_variant_inject(case)
            validation = CandidateVariantInjectRD.validate(cv_inject.toJsonDict(), verbose=True)
            self.assertTrue(validation.result, validation.messages)
            has_ig = True
        self.assertTrue(has_ig, "No interpreted genome")

        cr = case.get_clinical_report()
        has_cr = False
        if cr:
            self.assertTrue(ClinicalReportRD.validate(cr.toJsonDict()))
            rv_inject = CvaInjectionHelper.generate_reported_variant_inject(case)
            validation = ReportedVariantInjectRD.validate(rv_inject.toJsonDict(), verbose=True)
            self.assertTrue(validation.result, validation.messages)
            has_cr = True
        self.assertTrue(has_cr, "No clinical report")

        eq = case.get_exit_questionnaire()
        has_eq = False
        if eq:
            validation = RareDiseaseExitQuestionnaire.validate(eq.toJsonDict(), verbose=True)
            self.assertTrue(validation.result, validation.messages)
            eq_inject = CvaInjectionHelper.generate_exit_questionnaire_inject(case)
            validation = ExitQuestionnaireInjectRD.validate(eq_inject.toJsonDict(), verbose=True)
            self.assertTrue(validation.result, validation.messages)
            has_eq = True
        self.assertTrue(has_eq, "No exit questionnaire")

    def test_get_cancer_case(self):

        case_id = "124"
        case_version = 3
        case = self.cipapi.get_case(case_id, case_version)

        # compulsory fields
        ir = case.get_interpretation_request()
        validation = CancerInterpretationRequest.validate(ir.toJsonDict(), verbose=True)
        self.assertTrue(validation.result, validation.messages)
        tig = case.get_tiering_interpreted_genome()
        validation = CancerInterpretedGenome.validate(tig.toJsonDict(), verbose=True)
        self.assertTrue(validation.result, validation.messages)

        cr = case.get_clinical_report()
        has_cr = False
        if cr:
            validation = ClinicalReportCancer.validate(cr.toJsonDict(), verbose=True)
            self.assertTrue(validation.result, validation.messages)
            has_cr = True
        self.assertTrue(has_cr, "No clinical report")

        eq = case.get_exit_questionnaire()
        has_eq = False
        if eq:
            validation = CancerExitQuestionnaire.validate(eq.toJsonDict(), verbose=True)
            self.assertTrue(validation.result, validation.messages)
            eq_inject = CvaInjectionHelper.generate_exit_questionnaire_inject(case)
            validation = ExitQuestionnaireInjectCancer.validate(eq_inject.toJsonDict(), verbose=True)
            self.assertTrue(validation.result, validation.messages)
            has_eq = True
        self.assertTrue(has_eq, "No exit questionnaire")

    def test_all(self):

        ig_tested = {Program.rare_disease: False, Program.cancer: False}
        cr_tested = {Program.rare_disease: False, Program.cancer: False}
        eq_tested = {Program.rare_disease: False, Program.cancer: False}
        for case in self.cipapi.get_cases():
            logging.info("Case with id {} and version {} for program {}".format(
                case.case_id, case.case_version, case.program))
            # compulsory fields
            ir = case.get_interpretation_request()
            self.assertTrue(CancerInterpretationRequest.validate(ir.toJsonDict(), verbose=True))
            tig = case.get_tiering_interpreted_genome()
            self.assertTrue(CancerInterpretedGenome.validate(tig.toJsonDict(), verbose=True))

            if case.program == Program.rare_disease:
                ped = case.get_pedigree()
                self.assertTrue(Pedigree.validate(ped.toJsonDict(), verbose=True))

            # optional data
            try:
                ig = case.get_interpreted_genome()
                if ig:
                    if case.is_rare_disease():
                        self.assertTrue(CancerInterpretedGenome.validate(ig.toJsonDict(), verbose=True))
                    elif case.is_cancer():
                        self.assertTrue(InterpretedGenomeRD.validate(ig.toJsonDict(), verbose=True))
                    ig_tested[case.program] = True
            except MigrationError as ex:
                logging.warning("Migration error for interpreted genome for case with id {} and version {}: {}".format(
                    case.case_id, case.case_version, ex.message))

            try:
                cr = case.get_clinical_report()
                if cr:
                    if case.is_rare_disease():
                        self.assertTrue(ClinicalReportRD.validate(cr.toJsonDict(), verbose=True))
                    elif case.is_cancer():
                        self.assertTrue(ClinicalReportCancer.validate(cr.toJsonDict(), verbose=True))
                    cr_tested[case.program] = True
            except MigrationError as ex:
                logging.warning("Migration error for clinical report for case with id {} and version {}: {}".format(
                    case.case_id, case.case_version, ex.message))

            try:
                eq = case.get_exit_questionnaire()
                if eq:
                    if case.is_rare_disease():
                        self.assertTrue(CancerExitQuestionnaire.validate(cr.toJsonDict(), verbose=True))
                    elif case.is_cancer():
                        self.assertTrue(RareDiseaseExitQuestionnaire.validate(cr.toJsonDict(), verbose=True))
                    eq_tested[case.program] = True
            except MigrationError as ex:
                logging.warning("Migration error for exit questionnaire for case with id {} and version {}: {}".format(
                    case.case_id, case.case_version, ex.message))

        self.assertTrue(ig_tested[Program.rare_disease], "No rare disease case with interpreted genomes")
        self.assertTrue(cr_tested[Program.rare_disease], "No rare disease case with clinical reports")
        self.assertTrue(eq_tested[Program.rare_disease], "No rare disease case with exit questionnaires")
        self.assertTrue(cr_tested[Program.cancer], "No cancer case with clinical reports")
        self.assertTrue(eq_tested[Program.cancer], "No cancer case with exit questionnaires")

    def test_count_by_panel(self):

        panels = {}
        for case in self.cipapi.get_cases(assembly=Assembly.GRCh38, sample_type='raredisease'):
            if case.is_assembly_38() and case.is_rare_disease():
                ir = case.get_interpretation_request()
                for panel in ir.pedigree.analysisPanels:
                    panel_name = panel.panelName
                    if panel_name not in panels:
                        panels[panel_name] = set()
                    panels[panel_name].add(ir.pedigree.familyId)
        for panel, families in panels.iteritems():
            print("Panel '{}' has {} cases".format(panel, len(list(families))))

