#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class UserCredentialsVerifier:
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

    def test_user_provided_credentials(self):
        """
        SPECIFIC TASK: Test credentials provided by the user
        
        User provided credentials:
        - Administradores: kael1@lavadero.com, kael2@lavadero.com, kael3@lavadero.com, kael4@lavadero.com (contraseña: kael1331)  
        - Cliente: kael11@lavadero.com (contraseña: kael1331)
        
        Problems observed:
        1. Frontend shows "Error al iniciar sesión" when trying to login with kael1@lavadero.com/kael1331
        2. Main page shows "No hay lavaderos operativos en este momento"
        """
        print("\n🎯 TESTING USER PROVIDED CREDENTIALS...")
        print("=" * 70)
        
        results = {
            'super_admin_login': False,
            'user_credentials_found': {},
            'authentication_tests': {},
            'lavaderos_operativos': False,
            'existing_users_found': [],
            'existing_lavaderos_found': []
        }
        
        # Step 1: Login as Super Admin to check database
        print("\n1️⃣ Login as Super Admin to check database...")
        super_admin_success, super_admin_token, super_admin_user = self.test_login(
            "kearcangel@gmail.com", "K@#l1331", "Super Admin"
        )
        
        if super_admin_success and super_admin_token:
            results['super_admin_login'] = True
            print("✅ Super Admin login successful")
        else:
            print("❌ Super Admin login failed - cannot check database")
            return results
        
        # Step 2: Check what users currently exist in the system
        print("\n2️⃣ Checking existing users in the system...")
        
        # Get all admins
        admins_success, admins_data = self.run_test(
            "Get All Admins - Check existing users",
            "GET",
            "superadmin/admins",
            200,
            token=super_admin_token
        )
        
        if admins_success and isinstance(admins_data, list):
            print(f"✅ Found {len(admins_data)} admin users in system:")
            for admin in admins_data:
                email = admin.get('email')
                nombre = admin.get('nombre')
                estado = admin.get('lavadero', {}).get('estado_operativo', 'N/A')
                lavadero_nombre = admin.get('lavadero', {}).get('nombre', 'Sin lavadero')
                
                results['existing_users_found'].append({
                    'email': email,
                    'nombre': nombre,
                    'tipo': 'ADMIN',
                    'estado_lavadero': estado,
                    'lavadero_nombre': lavadero_nombre
                })
                
                print(f"   • {email} ({nombre}) - Lavadero: {lavadero_nombre} - Estado: {estado}")
        else:
            print("❌ Failed to get admin list")
        
        # Get credentials testing to see passwords
        print("\n   Checking available credentials...")
        cred_success, cred_data = self.run_test(
            "Get Available Credentials",
            "GET",
            "superadmin/credenciales-testing",
            200,
            token=super_admin_token
        )
        
        if cred_success and isinstance(cred_data, list):
            print(f"✅ Found {len(cred_data)} credentials available:")
            for cred in cred_data:
                email = cred.get('email')
                password = cred.get('password', 'N/A')
                print(f"   • {email} / {password}")
        else:
            print("❌ Failed to get credentials list")
        
        # Step 3: Test the specific credentials provided by the user
        print("\n3️⃣ Testing user provided credentials...")
        
        user_provided_credentials = [
            # Administradores
            {"email": "kael1@lavadero.com", "password": "kael1331", "tipo": "ADMIN"},
            {"email": "kael2@lavadero.com", "password": "kael1331", "tipo": "ADMIN"},
            {"email": "kael3@lavadero.com", "password": "kael1331", "tipo": "ADMIN"},
            {"email": "kael4@lavadero.com", "password": "kael1331", "tipo": "ADMIN"},
            # Cliente
            {"email": "kael11@lavadero.com", "password": "kael1331", "tipo": "CLIENTE"}
        ]
        
        for cred in user_provided_credentials:
            email = cred['email']
            password = cred['password']
            tipo = cred['tipo']
            
            print(f"\n   Testing {email} ({tipo})...")
            
            # Test login
            login_success, token, user_data = self.test_login(email, password, f"User Provided {tipo}")
            
            results['user_credentials_found'][email] = {
                'exists': login_success,
                'tipo': tipo,
                'login_successful': login_success,
                'user_data': user_data if login_success else None
            }
            
            if login_success:
                print(f"✅ {email} login SUCCESSFUL")
                print(f"   User: {user_data.get('nombre')} - Role: {user_data.get('rol')}")
                
                # Test additional endpoints for successful logins
                if token:
                    # Test dashboard stats
                    stats_success, stats_data = self.run_test(
                        f"Dashboard Stats ({email})",
                        "GET",
                        "dashboard/stats",
                        200,
                        token=token
                    )
                    
                    results['authentication_tests'][email] = {
                        'dashboard_stats': stats_success,
                        'stats_data': stats_data if stats_success else None
                    }
                    
                    if stats_success:
                        print(f"   Dashboard stats accessible: {stats_data}")
            else:
                print(f"❌ {email} login FAILED - User does not exist or wrong password")
        
        # Step 4: Check lavaderos operativos (public endpoint)
        print("\n4️⃣ Checking lavaderos operativos (public endpoint)...")
        
        lavaderos_success, lavaderos_data = self.run_test(
            "Get Lavaderos Operativos (Public)",
            "GET",
            "lavaderos-operativos",
            200
        )
        
        if lavaderos_success and isinstance(lavaderos_data, list):
            results['lavaderos_operativos'] = len(lavaderos_data) > 0
            results['existing_lavaderos_found'] = lavaderos_data
            
            if len(lavaderos_data) > 0:
                print(f"✅ Found {len(lavaderos_data)} lavaderos operativos:")
                for lavadero in lavaderos_data:
                    nombre = lavadero.get('nombre')
                    direccion = lavadero.get('direccion')
                    estado_operativo = lavadero.get('estado_operativo')
                    estado_apertura = lavadero.get('estado_apertura')
                    
                    print(f"   • {nombre} - {direccion}")
                    print(f"     Estado operativo: {estado_operativo}")
                    print(f"     Estado apertura: {estado_apertura}")
            else:
                print("❌ NO lavaderos operativos found")
                print("   This explains why the main page shows 'No hay lavaderos operativos en este momento'")
        else:
            print("❌ Failed to get lavaderos operativos")
        
        # Step 5: Check all lavaderos (Super Admin view)
        print("\n5️⃣ Checking all lavaderos (Super Admin view)...")
        
        all_lavaderos_success, all_lavaderos_data = self.run_test(
            "Get All Lavaderos (Super Admin)",
            "GET",
            "superadmin/lavaderos",
            200,
            token=super_admin_token
        )
        
        if all_lavaderos_success and isinstance(all_lavaderos_data, list):
            print(f"✅ Found {len(all_lavaderos_data)} total lavaderos in system:")
            
            estados_count = {}
            for lavadero in all_lavaderos_data:
                nombre = lavadero.get('nombre')
                admin_email = lavadero.get('admin_email')
                estado = lavadero.get('estado_operativo')
                
                if estado not in estados_count:
                    estados_count[estado] = 0
                estados_count[estado] += 1
                
                print(f"   • {nombre} (Admin: {admin_email}) - Estado: {estado}")
            
            print(f"\n   Estados summary:")
            for estado, count in estados_count.items():
                print(f"   • {estado}: {count} lavaderos")
                
            # Check why no lavaderos are ACTIVO
            activos = [l for l in all_lavaderos_data if l.get('estado_operativo') == 'ACTIVO']
            if len(activos) == 0:
                print("\n   ⚠️  NO LAVADEROS ACTIVOS FOUND")
                print("   This explains why /lavaderos-operativos returns empty list")
                print("   Possible solutions:")
                print("   1. Activate existing lavaderos using Super Admin toggle")
                print("   2. Create new lavaderos and activate them")
                print("   3. Check if existing admins have pending payments that need approval")
        else:
            print("❌ Failed to get all lavaderos")
        
        # Step 6: Summary and recommendations
        print("\n6️⃣ SUMMARY AND RECOMMENDATIONS...")
        print("=" * 60)
        
        # Check user credentials
        found_users = [email for email, data in results['user_credentials_found'].items() if data['exists']]
        missing_users = [email for email, data in results['user_credentials_found'].items() if not data['exists']]
        
        print(f"USER CREDENTIALS STATUS:")
        if found_users:
            print(f"✅ FOUND ({len(found_users)}): {', '.join(found_users)}")
        if missing_users:
            print(f"❌ MISSING ({len(missing_users)}): {', '.join(missing_users)}")
        
        print(f"\nLAVADEROS STATUS:")
        if results['lavaderos_operativos']:
            print(f"✅ {len(results['existing_lavaderos_found'])} lavaderos operativos found")
        else:
            print("❌ NO lavaderos operativos found")
            print("   This is why the main page shows 'No hay lavaderos operativos'")
        
        print(f"\nRECOMMENDATIONS:")
        if missing_users:
            print("1. CREATE MISSING USERS:")
            for email in missing_users:
                cred_data = next((c for c in user_provided_credentials if c['email'] == email), {})
                if cred_data.get('tipo') == 'ADMIN':
                    print(f"   - Create admin: {email} with lavadero")
                else:
                    print(f"   - Create client: {email}")
        
        if not results['lavaderos_operativos']:
            print("2. ACTIVATE LAVADEROS:")
            print("   - Use Super Admin toggle to activate existing lavaderos")
            print("   - Approve pending payments if any")
            print("   - Set lavaderos to 'esta_abierto: true' in configuration")
        
        return results

def main():
    print("🚀 Starting User Credentials Verification")
    print("=" * 50)
    
    verifier = UserCredentialsVerifier()
    
    # Run the specific test for user provided credentials
    results = verifier.test_user_provided_credentials()
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL TEST SUMMARY")
    print("="*60)
    print(f"Total tests run: {verifier.tests_run}")
    print(f"Tests passed: {verifier.tests_passed}")
    print(f"Tests failed: {verifier.tests_run - verifier.tests_passed}")
    print(f"Success rate: {(verifier.tests_passed/verifier.tests_run)*100:.1f}%")
    
    return results

if __name__ == "__main__":
    main()