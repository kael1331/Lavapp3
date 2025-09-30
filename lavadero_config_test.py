import requests
import sys
import json
from datetime import datetime

class LavaderoConfigTester:
    def __init__(self, base_url="https://lavadero-system.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, expect_json=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if expect_json and response.text:
                    try:
                        response_data = response.json()
                        print(f"   Response: {json.dumps(response_data, indent=2)}")
                        return success, response_data
                    except:
                        print(f"   Response (text): {response.text}")
                        return success, response.text
                else:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, email, password, role_name):
        """Test login and get token"""
        success, response = self.run_test(
            f"Login as {role_name}",
            "POST",
            "login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            return True, response['access_token'], response['user']
        return False, None, None

    def test_lavadero_configuration_verification(self):
        """
        SPECIFIC TASK: Verify lavadero configurations to understand reservation system issues
        
        Requirements from review request:
        1. Get configuration for Lavadero Express (Carlos - kael4@lavadero.com)
        2. Get configuration for Lavadero Norte (Ana - kael1@lavadero.com) 
        3. Compare differences between configurations
        4. Verify non-working days for each lavadero
        
        Problem: Reservation calendar not respecting specific configuration of each lavadero
        
        Available credentials:
        - Ana (Lavadero Norte): kael1@lavadero.com / kael1331
        - Carlos (Lavadero Express): kael4@lavadero.com / kael1331
        """
        print("\n🎯 TESTING LAVADERO CONFIGURATION VERIFICATION...")
        print("=" * 70)
        print("OBJETIVO: Verificar configuraciones específicas de cada lavadero")
        print("PROBLEMA: El calendario de reservas no respeta la configuración específica")
        print("=" * 70)
        
        results = {
            'ana_login': False,
            'carlos_login': False,
            'ana_lavadero_id': None,
            'carlos_lavadero_id': None,
            'ana_config': None,
            'carlos_config': None,
            'ana_dias_no_laborales': None,
            'carlos_dias_no_laborales': None,
            'configurations_different': False,
            'config_comparison': {}
        }
        
        # Step 1: Login as Ana (Lavadero Norte)
        print("\n1️⃣ Login as Ana (Lavadero Norte - kael1@lavadero.com)...")
        ana_login_success, ana_token, ana_user = self.test_login(
            "kael1@lavadero.com", "kael1331", "Ana - Lavadero Norte"
        )
        
        if ana_login_success and ana_token:
            results['ana_login'] = True
            print("✅ Ana login successful")
            print(f"   User ID: {ana_user.get('id')}")
            print(f"   Nombre: {ana_user.get('nombre')}")
            print(f"   Rol: {ana_user.get('rol')}")
        else:
            print("❌ Ana login failed")
            return results
        
        # Step 2: Login as Carlos (Lavadero Express)
        print("\n2️⃣ Login as Carlos (Lavadero Express - kael4@lavadero.com)...")
        carlos_login_success, carlos_token, carlos_user = self.test_login(
            "kael4@lavadero.com", "kael1331", "Carlos - Lavadero Express"
        )
        
        if carlos_login_success and carlos_token:
            results['carlos_login'] = True
            print("✅ Carlos login successful")
            print(f"   User ID: {carlos_user.get('id')}")
            print(f"   Nombre: {carlos_user.get('nombre')}")
            print(f"   Rol: {carlos_user.get('rol')}")
        else:
            print("❌ Carlos login failed")
            return results
        
        # Step 3: Get Ana's lavadero ID and configuration
        print("\n3️⃣ Getting Ana's lavadero configuration...")
        
        # First get dashboard stats to find lavadero info
        ana_stats_success, ana_stats = self.run_test(
            "Get Ana's Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            token=ana_token
        )
        
        if ana_stats_success and isinstance(ana_stats, dict):
            print("✅ Ana's dashboard stats retrieved")
            print(f"   Lavadero: {ana_stats.get('lavadero_nombre')}")
            print(f"   Estado: {ana_stats.get('estado_operativo')}")
            print(f"   Días restantes: {ana_stats.get('dias_restantes')}")
        
        # Get Ana's lavadero configuration via admin endpoint
        ana_config_success, ana_config = self.run_test(
            "Get Ana's Lavadero Configuration",
            "GET",
            "admin/configuracion",
            200,
            token=ana_token
        )
        
        if ana_config_success and isinstance(ana_config, dict):
            results['ana_config'] = ana_config
            results['ana_lavadero_id'] = ana_config.get('lavadero_id')
            print("✅ Ana's configuration retrieved")
            print(f"   Lavadero ID: {results['ana_lavadero_id']}")
            print(f"   Horario apertura: {ana_config.get('hora_apertura')}")
            print(f"   Horario cierre: {ana_config.get('hora_cierre')}")
            print(f"   Duración turno: {ana_config.get('duracion_turno_minutos')} minutos")
            print(f"   Días laborales: {ana_config.get('dias_laborales')}")
            print(f"   Precio turno: ${ana_config.get('precio_turno')}")
        else:
            print("❌ Failed to get Ana's configuration")
        
        # Step 4: Get Carlos's lavadero ID and configuration
        print("\n4️⃣ Getting Carlos's lavadero configuration...")
        
        # First get dashboard stats to find lavadero info
        carlos_stats_success, carlos_stats = self.run_test(
            "Get Carlos's Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            token=carlos_token
        )
        
        if carlos_stats_success and isinstance(carlos_stats, dict):
            print("✅ Carlos's dashboard stats retrieved")
            print(f"   Lavadero: {carlos_stats.get('lavadero_nombre')}")
            print(f"   Estado: {carlos_stats.get('estado_operativo')}")
            print(f"   Días restantes: {carlos_stats.get('dias_restantes')}")
        
        # Get Carlos's lavadero configuration via admin endpoint
        carlos_config_success, carlos_config = self.run_test(
            "Get Carlos's Lavadero Configuration",
            "GET",
            "admin/configuracion",
            200,
            token=carlos_token
        )
        
        if carlos_config_success and isinstance(carlos_config, dict):
            results['carlos_config'] = carlos_config
            results['carlos_lavadero_id'] = carlos_config.get('lavadero_id')
            print("✅ Carlos's configuration retrieved")
            print(f"   Lavadero ID: {results['carlos_lavadero_id']}")
            print(f"   Horario apertura: {carlos_config.get('hora_apertura')}")
            print(f"   Horario cierre: {carlos_config.get('hora_cierre')}")
            print(f"   Duración turno: {carlos_config.get('duracion_turno_minutos')} minutos")
            print(f"   Días laborales: {carlos_config.get('dias_laborales')}")
            print(f"   Precio turno: ${carlos_config.get('precio_turno')}")
        else:
            print("❌ Failed to get Carlos's configuration")
        
        # Step 5: Test public lavadero configuration endpoints
        print("\n5️⃣ Testing public lavadero configuration endpoints...")
        
        if results['ana_lavadero_id']:
            ana_public_config_success, ana_public_config = self.run_test(
                f"Get Ana's Public Configuration (ID: {results['ana_lavadero_id']})",
                "GET",
                f"lavaderos/{results['ana_lavadero_id']}/configuracion",
                200
            )
            
            if ana_public_config_success:
                print("✅ Ana's public configuration accessible")
                print(f"   Horario: {ana_public_config.get('horario_apertura')} - {ana_public_config.get('horario_cierre')}")
                print(f"   Duración turno: {ana_public_config.get('duracion_turno')} minutos")
                print(f"   Días laborables: {ana_public_config.get('dias_laborables')}")
                print(f"   Está abierto: {ana_public_config.get('esta_abierto')}")
        
        if results['carlos_lavadero_id']:
            carlos_public_config_success, carlos_public_config = self.run_test(
                f"Get Carlos's Public Configuration (ID: {results['carlos_lavadero_id']})",
                "GET",
                f"lavaderos/{results['carlos_lavadero_id']}/configuracion",
                200
            )
            
            if carlos_public_config_success:
                print("✅ Carlos's public configuration accessible")
                print(f"   Horario: {carlos_public_config.get('horario_apertura')} - {carlos_public_config.get('horario_cierre')}")
                print(f"   Duración turno: {carlos_public_config.get('duracion_turno')} minutos")
                print(f"   Días laborables: {carlos_public_config.get('dias_laborables')}")
                print(f"   Está abierto: {carlos_public_config.get('esta_abierto')}")
        
        # Step 6: Get días no laborales for Ana
        print("\n6️⃣ Getting días no laborales for Ana...")
        ana_dias_success, ana_dias = self.run_test(
            "Get Ana's Días No Laborales",
            "GET",
            "admin/dias-no-laborales",
            200,
            token=ana_token
        )
        
        if ana_dias_success and isinstance(ana_dias, list):
            results['ana_dias_no_laborales'] = ana_dias
            print(f"✅ Ana's días no laborales retrieved - {len(ana_dias)} días encontrados")
            for i, dia in enumerate(ana_dias[:3]):  # Show first 3
                print(f"   Día {i+1}: {dia.get('fecha')} - {dia.get('motivo', 'Sin motivo')}")
        else:
            print("❌ Failed to get Ana's días no laborales")
        
        # Step 7: Get días no laborales for Carlos
        print("\n7️⃣ Getting días no laborales for Carlos...")
        carlos_dias_success, carlos_dias = self.run_test(
            "Get Carlos's Días No Laborales",
            "GET",
            "admin/dias-no-laborales",
            200,
            token=carlos_token
        )
        
        if carlos_dias_success and isinstance(carlos_dias, list):
            results['carlos_dias_no_laborales'] = carlos_dias
            print(f"✅ Carlos's días no laborales retrieved - {len(carlos_dias)} días encontrados")
            for i, dia in enumerate(carlos_dias[:3]):  # Show first 3
                print(f"   Día {i+1}: {dia.get('fecha')} - {dia.get('motivo', 'Sin motivo')}")
        else:
            print("❌ Failed to get Carlos's días no laborales")
        
        # Step 8: Compare configurations
        print("\n8️⃣ COMPARING CONFIGURATIONS BETWEEN LAVADEROS...")
        print("=" * 60)
        
        if results['ana_config'] and results['carlos_config']:
            ana_cfg = results['ana_config']
            carlos_cfg = results['carlos_config']
            
            comparison_fields = [
                'hora_apertura',
                'hora_cierre', 
                'duracion_turno_minutos',
                'dias_laborales',
                'precio_turno',
                'alias_bancario'
            ]
            
            differences_found = False
            
            print("COMPARACIÓN DETALLADA:")
            print(f"{'Campo':<25} {'Ana (Norte)':<20} {'Carlos (Express)':<20} {'¿Diferente?'}")
            print("-" * 80)
            
            for field in comparison_fields:
                ana_value = ana_cfg.get(field, 'N/A')
                carlos_value = carlos_cfg.get(field, 'N/A')
                different = ana_value != carlos_value
                
                if different:
                    differences_found = True
                
                diff_indicator = "❌ SÍ" if different else "✅ NO"
                print(f"{field:<25} {str(ana_value):<20} {str(carlos_value):<20} {diff_indicator}")
                
                results['config_comparison'][field] = {
                    'ana': ana_value,
                    'carlos': carlos_value,
                    'different': different
                }
            
            results['configurations_different'] = differences_found
            
            print("\n" + "=" * 60)
            if differences_found:
                print("🔍 DIFERENCIAS ENCONTRADAS ENTRE CONFIGURACIONES")
                print("   Esto podría explicar por qué el calendario no funciona igual para ambos lavaderos")
            else:
                print("⚠️  NO SE ENCONTRARON DIFERENCIAS EN CONFIGURACIONES BÁSICAS")
                print("   El problema podría estar en otro lado (días no laborales, estado de apertura, etc.)")
        
        # Step 9: Compare días no laborales
        print("\n9️⃣ COMPARING DÍAS NO LABORALES...")
        
        if results['ana_dias_no_laborales'] is not None and results['carlos_dias_no_laborales'] is not None:
            ana_dias_count = len(results['ana_dias_no_laborales'])
            carlos_dias_count = len(results['carlos_dias_no_laborales'])
            
            print(f"Ana (Norte): {ana_dias_count} días no laborales")
            print(f"Carlos (Express): {carlos_dias_count} días no laborales")
            
            if ana_dias_count != carlos_dias_count:
                print("❌ DIFERENCIA EN CANTIDAD DE DÍAS NO LABORALES")
                print("   Esto podría afectar la disponibilidad del calendario")
            else:
                print("✅ Misma cantidad de días no laborales")
        
        # Step 10: Final summary and recommendations
        print("\n🔟 RESUMEN Y RECOMENDACIONES...")
        print("=" * 60)
        
        print("ESTADO DE PRUEBAS:")
        test_results = [
            ("Login Ana", results['ana_login']),
            ("Login Carlos", results['carlos_login']),
            ("Configuración Ana", results['ana_config'] is not None),
            ("Configuración Carlos", results['carlos_config'] is not None),
            ("Días no laborales Ana", results['ana_dias_no_laborales'] is not None),
            ("Días no laborales Carlos", results['carlos_dias_no_laborales'] is not None)
        ]
        
        for test_name, test_result in test_results:
            status = "✅" if test_result else "❌"
            print(f"   {status} {test_name}")
        
        print("\nHALLAZGOS PRINCIPALES:")
        if results['configurations_different']:
            print("❌ Las configuraciones de los lavaderos SON DIFERENTES")
            print("   Campos con diferencias:")
            for field, comparison in results['config_comparison'].items():
                if comparison['different']:
                    print(f"   • {field}: Ana='{comparison['ana']}' vs Carlos='{comparison['carlos']}'")
        else:
            print("✅ Las configuraciones básicas son iguales")
        
        print("\nRECOMENDACIONES:")
        if results['configurations_different']:
            print("1. Verificar que el frontend esté usando la configuración correcta para cada lavadero")
            print("2. Revisar el endpoint GET /lavaderos/{id}/configuracion en el calendario")
            print("3. Asegurar que el lavadero_id se pase correctamente al generar turnos")
        else:
            print("1. Las configuraciones básicas son iguales, buscar otras causas:")
            print("   • Estado de apertura (esta_abierto)")
            print("   • Días no laborales específicos")
            print("   • Lógica de generación de turnos en el frontend")
        
        return results

    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 Test Summary:")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "   Success rate: 0%")

if __name__ == "__main__":
    tester = LavaderoConfigTester()
    
    print("🎯 LAVADERO CONFIGURATION VERIFICATION TEST")
    print("=" * 50)
    print("Testing specific lavadero configurations to understand reservation system issues")
    print("=" * 50)
    
    # Run the specific configuration verification test
    results = tester.test_lavadero_configuration_verification()
    
    # Print summary
    tester.print_summary()
    
    print("\n" + "=" * 50)
    print("🏁 TESTING COMPLETE")
    print("=" * 50)