# hardware_check/middleware.py
import subprocess
import platform
import os
import json
import hashlib
import datetime
from django.http import HttpResponse, JsonResponse
from django.conf import settings

class HardwareVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.config_file = os.path.join(settings.BASE_DIR, 'hardware_config.json')
        
        # Load or create the authorized hardware signatures
        self.config_data = self.load_config()
        self.authorized_devices = self.config_data.get('authorized_devices', [])
        self.master_password = self.config_data.get('master_password', None)
        
    def __call__(self, request):
        # Special route to add a new device (with password protection)
        if request.path == '/hardware/add_device/':
            return self.add_device(request)
        
        # Special route to list authorized devices (also protected)
        if request.path == '/hardware/list_devices/':
            return self.list_devices(request)
            
        # Get current hardware signature
        current_signature = self.get_hardware_signature()
        
        # Check if current signature is in authorized devices
        is_authorized = False
        for device in self.authorized_devices:
            if current_signature == device['signature']:
                is_authorized = True
                break
                
        if not is_authorized:
            return self.generate_error_response(current_signature)
        
        # Hardware verified, proceed with request
        return self.get_response(request)
    
    def get_hardware_identifiers(self):
        """Get raw hardware identifiers from the system"""
        system = platform.system()
        hardware_info = {
            'disk_id': 'unknown',
            'cpu_id': 'unknown',
            'motherboard_id': 'unknown',
            'memory_id': 'unknown'
        }
        
        try:
            if system == "Windows":
                # Get disk ID
                result = subprocess.check_output("wmic diskdrive get SerialNumber", shell=True)
                hardware_info['disk_id'] = result.decode().strip().split('\n')[1].strip()
                
                # Get CPU ID
                result = subprocess.check_output("wmic cpu get ProcessorId", shell=True)
                hardware_info['cpu_id'] = result.decode().strip().split('\n')[1].strip()
                
                # Get motherboard ID
                result = subprocess.check_output("wmic baseboard get SerialNumber", shell=True)
                hardware_info['motherboard_id'] = result.decode().strip().split('\n')[1].strip()
                
                # Get memory ID
                result = subprocess.check_output("wmic memorychip get SerialNumber", shell=True)
                hardware_info['memory_id'] = result.decode().strip().split('\n')[1].strip()
                
            elif system == "Linux":
                # Get disk ID
                result = subprocess.check_output("lsblk --nodeps -o SERIAL | head -2", shell=True)
                hardware_info['disk_id'] = result.decode().strip().split('\n')[1].strip()
                
                # Get CPU ID
                result = subprocess.check_output("cat /proc/cpuinfo | grep -i 'processor' | head -1", shell=True)
                hardware_info['cpu_id'] = result.decode().strip()
                
                # Get motherboard ID
                try:
                    result = subprocess.check_output("cat /sys/class/dmi/id/board_serial", shell=True)
                    hardware_info['motherboard_id'] = result.decode().strip()
                except:
                    try:
                        result = subprocess.check_output("sudo dmidecode -s baseboard-serial-number", shell=True)
                        hardware_info['motherboard_id'] = result.decode().strip()
                    except:
                        pass
                
                # Get memory ID
                try:
                    result = subprocess.check_output("sudo dmidecode -t memory | grep -i 'Serial Number' | head -1", shell=True)
                    hardware_info['memory_id'] = result.decode().strip().split(':')[1].strip()
                except:
                    pass
                
            elif system == "Darwin":  # macOS
                # Get system hardware UUID
                result = subprocess.check_output("system_profiler SPHardwareDataType | grep 'Hardware UUID'", shell=True)
                uuid = result.decode().strip().split(':')[1].strip()
                hardware_info['disk_id'] = uuid
                
                # Get serial number
                result = subprocess.check_output("system_profiler SPHardwareDataType | grep 'Serial Number'", shell=True)
                serial = result.decode().strip().split(':')[1].strip()
                hardware_info['motherboard_id'] = serial
                
                # CPU info
                result = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True)
                hardware_info['cpu_id'] = result.decode().strip()
                
                # Memory info
                result = subprocess.check_output("system_profiler SPMemoryDataType | grep -i 'Serial Number' | head -1", shell=True)
                hardware_info['memory_id'] = result.decode().strip()
        
        except Exception as e:
            print(f"Error getting hardware info: {e}")
            
        return hardware_info
    
    def get_hardware_signature(self):
        """Generate a signature from hardware identifiers"""
        identifiers = self.get_hardware_identifiers()
        
        # Create a combined string of all hardware identifiers
        combined = "".join(str(v) for v in identifiers.values())
        
        # Create a signature using SHA-256
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def load_config(self):
        """Load or create configuration file with master password"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                return config
            except Exception as e:
                print(f"Error loading hardware config: {e}")
                return {'authorized_devices': [], 'master_password': None}
        
        # First run - create config with master password and first device
        print("First run detected. Creating hardware signature...")
        signature = self.get_hardware_signature()
        
        # Use the hardware signature as the master password
        master_password = signature
        
        # Create first device entry
        devices = [{
            'name': 'Initial Device',
            'signature': signature,
            'added_on': datetime.datetime.now().strftime('%Y-%m-%d')
        }]
        
        config = {
            'authorized_devices': devices,
            'master_password': master_password
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Hardware config created - your device is now the master device")
            print(f"Your hardware signature is: {signature}")
            print("IMPORTANT: Save this signature as it is your master password for authorizing future devices!")
        except Exception as e:
            print(f"Error saving hardware config: {e}")
        
        return config
    
    def save_config(self):
        """Save the current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    'authorized_devices': self.authorized_devices,
                    'master_password': self.master_password
                }, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving hardware config: {e}")
            return False
    
    def add_device(self, request):
        """Add current device to authorized devices (password protected)"""
        password = request.GET.get('password', '')
        device_name = request.GET.get('name', 'Unnamed Device')
        
        # Verify master password
        if not password or password != self.master_password:
            return JsonResponse({
                'success': False,
                'message': 'Invalid master password'
            }, status=403)
        
        current_signature = self.get_hardware_signature()
        
        # Check if device already exists
        for device in self.authorized_devices:
            if current_signature == device['signature']:
                return JsonResponse({
                    'success': False,
                    'message': f'This device is already authorized as "{device["name"]}"'
                })
        
        # Add new device
        self.authorized_devices.append({
            'name': device_name,
            'signature': current_signature,
            'added_on': datetime.datetime.now().strftime('%Y-%m-%d')
        })
        
        # Save updated list
        if self.save_config():
            return JsonResponse({
                'success': True,
                'message': f'Device "{device_name}" has been authorized',
                'device': {
                    'name': device_name,
                    'signature': current_signature
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error saving device configuration'
            })
    
    def list_devices(self, request):
        """List all authorized devices (password protected)"""
        password = request.GET.get('password', '')
        
        # Verify master password
        if not password or password != self.master_password:
            return JsonResponse({
                'success': False,
                'message': 'Invalid master password'
            }, status=403)
            
        current_signature = self.get_hardware_signature()
        devices_info = []
        
        for device in self.authorized_devices:
            devices_info.append({
                'name': device['name'],
                'signature': device['signature'][:10] + '...',  # Show only part of the signature
                'added_on': device.get('added_on', 'Unknown'),
                'is_current_device': device['signature'] == current_signature
            })
            
        return JsonResponse({
            'devices': devices_info,
            'current_device_authorized': any(d['signature'] == current_signature for d in self.authorized_devices)
        })
    
    def generate_error_response(self, current_signature):
        """Generate error page with hardware verification details"""
        hardware_info = self.get_hardware_identifiers()
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Unauthorized Device</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f8f8f8; }
                .container { max-width: 800px; margin: 0 auto; background-color: #fff; 
                             padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
                h1 { color: #d9534f; margin-top: 0; }
                .component { margin-bottom: 15px; padding: 15px; border-radius: 5px; 
                            background-color: #f2dede; border-left: 5px solid #d9534f; }
                .signatures { margin-top: 30px; padding: 15px; background-color: #eee; border-radius: 5px; }
                .title { font-weight: bold; margin-bottom: 5px; }
                .authorize-form { margin-top: 30px; padding: 15px; background-color: #dff0d8; 
                                 border-radius: 5px; border-left: 5px solid #5cb85c; display: none; }
                input, button { padding: 10px; margin: 5px 0; }
                button { background-color: #5cb85c; color: white; border: none; cursor: pointer; }
                .show-form-btn { background-color: #5bc0de; margin-top: 20px; }
            </style>
            <script>
                function showAuthForm() {
                    document.getElementById('auth-form').style.display = 'block';
                    document.getElementById('show-form-btn').style.display = 'none';
                }
            </script>
        </head>
        <body>
            <div class="container">
                <h1>Unauthorized Device Detected</h1>
                <p>This application is licensed to run only on authorized devices.</p>
                
                <h2>Current Hardware Information:</h2>
        """
        
        for component, value in hardware_info.items():
            html_content += f"""
                <div class="component">
                    <div class="title">{component.replace('_', ' ').title()}:</div>
                    <div>{value or 'Not available'}</div>
                </div>
            """
        
        html_content += f"""
                <div class="signatures">
                    <div class="title">Hardware Signature:</div>
                    <div>Current device: {current_signature}</div>
                </div>
                
                <button id="show-form-btn" class="show-form-btn" onclick="showAuthForm()">I Have Authorization Access</button>
                
                <div id="auth-form" class="authorize-form">
                    <div class="title">Authorize This Device:</div>
                    <p>Enter the master password (the hardware signature of the master device) and a device name to authorize this device:</p>
                    <form action="/hardware/add_device/" method="get">
                        <input type="password" name="password" placeholder="Master Password" required>
                        <input type="text" name="name" placeholder="Device Name" required>
                        <button type="submit">Authorize This Device</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html_content, status=403)
