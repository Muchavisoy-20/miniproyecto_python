import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from feature_toggle_service import (
    METRICS,
    SIMULATED_CONFIG,
    ToggleConfig,
    activate_emergency_kill_switch,
    evaluate_feature_toggle,
    get_metrics_dashboard,
    process_checkout,
    CheckoutRequest,
)


class TestFeatureToggleGovernance(unittest.TestCase):

    def setUp(self):
        # Resetear estado antes de cada prueba
        SIMULATED_CONFIG.is_active = True
        SIMULATED_CONFIG.percentage_rollout = 0
        SIMULATED_CONFIG.allowlist_emails = ["admin@coworking.com", "dev@coworking.com"]
        SIMULATED_CONFIG.allowlist_domains = ["coworking.com"]

        METRICS["total_requests"] = 0
        METRICS["express_attempts"] = 0
        METRICS["express_success"] = 0
        METRICS["express_errors"] = 0
        METRICS["classic_attempts"] = 0
        METRICS["classic_success"] = 0
        METRICS["latencies_ms"] = []

    def test_default_user_gets_classic_flow_when_rollout_is_zero(self):
        """Usuarios externos reciben el flujo tradicional cuando el toggle está al 0%."""
        external_user = "cliente_externo@gmail.com"
        self.assertFalse(evaluate_feature_toggle(external_user))

        req = CheckoutRequest(user_email=external_user, space_id=1, amount=25.0)
        resp = process_checkout(req)
        self.assertEqual(resp["flow"], "PAGO_TRADICIONAL_3_PASOS")

    def test_internal_allowlisted_user_gets_express_flow(self):
        """Los correos corporativos o en lista blanca tienen acceso a Pagos Express sin importar el porcentaje."""
        internal_user = "qa_lead@coworking.com"
        self.assertTrue(evaluate_feature_toggle(internal_user))

        req = CheckoutRequest(user_email=internal_user, space_id=1, amount=25.0)
        resp = process_checkout(req)
        self.assertEqual(resp["flow"], "PAGOS_EXPRESS_1_CLICK")

    def test_full_rollout_enables_all_users(self):
        """Al configurar el rollout al 100%, todos los clientes reciben Pagos Express."""
        SIMULATED_CONFIG.percentage_rollout = 100
        external_user = "comprador@hotmail.com"
        self.assertTrue(evaluate_feature_toggle(external_user))

        req = CheckoutRequest(user_email=external_user, space_id=1, amount=40.0)
        resp = process_checkout(req)
        self.assertEqual(resp["flow"], "PAGOS_EXPRESS_1_CLICK")

    def test_emergency_kill_switch_instantly_disables_express(self):
        """El Kill-Switch apaga la funcionalidad en caliente para todos los usuarios."""
        SIMULATED_CONFIG.percentage_rollout = 100
        user = "test_emergency@coworking.com"

        # Activado inicialmente
        self.assertTrue(evaluate_feature_toggle(user))

        # Disparar Kill-Switch de emergencia
        activate_emergency_kill_switch()

        # Debe evaluar inmediatamente a False
        self.assertFalse(evaluate_feature_toggle(user))
        self.assertFalse(SIMULATED_CONFIG.is_active)
        self.assertEqual(SIMULATED_CONFIG.percentage_rollout, 0)

    def test_observability_dashboard_detects_error_threshold(self):
        """El cuadro de mando calcula el porcentaje de error y alerta sobre necesidad de Kill-Switch."""
        SIMULATED_CONFIG.percentage_rollout = 100

        # Procesar transacciones exitosas
        for i in range(10):
            req = CheckoutRequest(user_email=f"user_{i}@test.com", space_id=1, amount=25.0)
            process_checkout(req)

        # Simular 2 errores críticos
        for j in range(2):
            try:
                req_fail = CheckoutRequest(
                    user_email=f"fail_{j}@test.com", space_id=1, amount=25.0, simulate_failure=True
                )
                process_checkout(req_fail)
            except Exception:
                pass

        dashboard = get_metrics_dashboard()
        self.assertEqual(dashboard["express_payments"]["attempts"], 12)
        self.assertEqual(dashboard["express_payments"]["errors"], 2)
        # Error rate = 2/12 = 16.67% > 1.5% -> Dispara Kill-Switch alert
        self.assertTrue(dashboard["kill_switch_recommended"])
        self.assertIn("CRITICAL_ALERT", dashboard["system_health"])


if __name__ == "__main__":
    unittest.main()
