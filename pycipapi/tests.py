import os
import logging
from unittest import TestCase

from protocols.migration.base_migration import MigrationError
from protocols.reports_5_0_0 import Program, ClinicalReportCancer
from protocols.cva_1_0_0 import ReportEventType, Assembly, Variant
from protocols.reports_5_0_0 import InterpretedGenomeRD, ClinicalReportRD, CancerInterpretationRequest, \
    CancerInterpretedGenome, RareDiseaseExitQuestionnaire, CancerExitQuestionnaire, InterpretationRequestRD
from protocols.participant_1_1_0 import Pedigree

from pycipapi.cipapi_client import CipApiClient, CipApiCase


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

        case_id = "29"
        case_version = 2
        case = self.cipapi.get_case(case_id, case_version)

        # compulsory fields
        ir = case.get_interpretation_request()
        self.assertTrue(InterpretationRequestRD.validate(ir.toJsonDict()))
        tig = case.get_tiering_interpreted_genome()
        self.assertTrue(InterpretedGenomeRD.validate(tig.toJsonDict()))
        ped = case.get_pedigree()
        self.assertTrue(Pedigree.validate(ped.toJsonDict()))

        # optional data
        ig = case.get_interpreted_genome()
        if ig:
            self.assertTrue(InterpretedGenomeRD.validate(ig.toJsonDict()))
        cr = case.get_clinical_report()
        if cr:
            self.assertTrue(ClinicalReportRD.validate(cr.toJsonDict()))
        eq = case.get_exit_questionnaire_rd()
        if eq:
            self.assertTrue(RareDiseaseExitQuestionnaire.validate(cr.toJsonDict()))

    def test_get_cancer_case(self):

        case_id = "39"
        case_version = 1
        case = self.cipapi.get_case(case_id, case_version)

        # compulsory fields
        ir = case.get_interpretation_request()
        self.assertTrue(CancerInterpretationRequest.validate(ir.toJsonDict()))
        tig = case.get_tiering_interpreted_genome()
        self.assertTrue(CancerInterpretedGenome.validate(tig.toJsonDict()))

        # optional data
        ig = case.get_interpreted_genome()
        if ig:
            self.assertTrue(CancerInterpretedGenome.validate(ig.toJsonDict()))
        cr = case.get_clinical_report()
        if cr:
            self.assertTrue(ClinicalReportCancer.validate(cr.toJsonDict()))
        eq = case.get_exit_questionnaire_rd()
        if eq:
            self.assertTrue(RareDiseaseExitQuestionnaire.validate(cr.toJsonDict()))

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
                    self.assertTrue(CancerInterpretedGenome.validate(ig.toJsonDict(), verbose=True))
                    ig_tested[case.program] = True
            except MigrationError, ex:
                logging.warning("Migration error for interpreted genome for case with id {} and version {}: {}".format(
                    case.case_id, case.case_version, ex.message))

            try:
                cr = case.get_clinical_report()
                if cr:
                    self.assertTrue(ClinicalReportCancer.validate(cr.toJsonDict(), verbose=True))
                    cr_tested[case.program] = True
            except MigrationError, ex:
                logging.warning("Migration error for clinical report for case with id {} and version {}: {}".format(
                    case.case_id, case.case_version, ex.message))

            try:
                eq = case.get_exit_questionnaire_rd()
                if eq:
                    self.assertTrue(RareDiseaseExitQuestionnaire.validate(cr.toJsonDict(), verbose=True))
                    eq_tested[case.program] = True
            except MigrationError, ex:
                logging.warning("Migration error for exit questionnaire for case with id {} and version {}: {}".format(
                    case.case_id, case.case_version, ex.message))

        self.assertTrue(ig_tested[Program.rare_disease], "No rare disease case with interpreted genomes")
        self.assertTrue(cr_tested[Program.rare_disease], "No rare disease case with clinical reports")
        self.assertTrue(eq_tested[Program.rare_disease], "No rare disease case with exit questionnaires")
        self.assertTrue(ig_tested[Program.cancer], "No cancer case with interpreted genomes")
        self.assertTrue(cr_tested[Program.cancer], "No cancer case with clinical reports")
        self.assertTrue(eq_tested[Program.cancer], "No cancer case with exit questionnaires")
