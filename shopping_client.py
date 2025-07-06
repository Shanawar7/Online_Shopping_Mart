from colorama import Style, init, Fore, Back
import socket
import json
import sys
import time
from datetime import datetime

init(autoreset=True)

class ShoppingMartClient:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.current_user = None
        self.connected = False

    def animated_loading(self, message, duration=1.5):
        """Enhanced loading animation with colors"""
        print(Fore.CYAN + message, end="", flush=True)
        
        # Spinning animation
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        end_time = time.time() + duration
        
        while time.time() < end_time:
            for char in spinner:
                print(f"\r{Fore.CYAN}{message} {Fore.YELLOW}{char}", end="", flush=True)
                time.sleep(0.1)
                if time.time() >= end_time:
                    break
        
        print(f"\r{message} {Fore.GREEN}✓" + Style.RESET_ALL)

    def typewriter_effect(self, text, color=Fore.WHITE, delay=0.03):
        """Typewriter effect for text"""
        for char in text:
            print(color + char, end='', flush=True)
            time.sleep(delay)
        print(Style.RESET_ALL)

    def connect_to_server(self):
        """Connect to the shopping mart server with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        self.animated_loading(f"🔌 Connecting to {self.host}:{self.port}")
       
        for attempt in range(max_retries):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10)  # 10 second timeout
                self.socket.connect((self.host, self.port))
                self.connected = True
                
                # Success animation
                print(Fore.GREEN + "✅ " + Back.GREEN + Fore.BLACK + " CONNECTED " + Style.RESET_ALL + 
                      Fore.GREEN + f" to Shopping Mart Server at {self.host}:{self.port}")
                return True
                
            except socket.timeout:
                print(Fore.YELLOW + f"⏱️  Connection timeout (attempt {attempt + 1}/{max_retries})")
            except ConnectionRefusedError:
                print(Fore.RED + f"❌ Connection refused. Server might not be running (attempt {attempt + 1}/{max_retries})")
            except socket.gaierror:
                print(Fore.RED + f"❌ Invalid host address: {self.host}")
                return False
            except Exception as e:
                print(Fore.RED + f"❌ Connection failed: {e} (attempt {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                self.animated_loading(f"🔄 Retrying in {retry_delay} seconds", retry_delay)
        
        print(Fore.RED + Back.RED + Fore.WHITE + " CONNECTION FAILED " + Style.RESET_ALL + 
              Fore.RED + " Unable to connect after multiple attempts")
        return False

    def send_request(self, request_data):
        """Send request to server and receive response with error handling"""
        try:
            if not self.connected:
                print(Fore.RED + "❌ Not connected to server")
                return None
            
            # Send request with animation
            request_json = json.dumps(request_data)
            self.socket.send(request_json.encode('utf-8'))
            
            # Show processing animation
            print(Fore.CYAN + "📡 Processing request", end="", flush=True)
            for _ in range(3):
                print(".", end="", flush=True)
                time.sleep(0.2)
            print(Style.RESET_ALL)
            
            # Receive response with timeout
            self.socket.settimeout(30)  # 30 second timeout for response
            response_data = self.socket.recv(4096).decode('utf-8')
            
            if not response_data:
                print(Fore.RED + "❌ Server closed connection")
                self.connected = False
                return None
            
            response = json.loads(response_data)
            return response
            
        except socket.timeout:
            print(Fore.YELLOW + "⏱️  Request timed out")
            return None
        except ConnectionResetError:
            print(Fore.RED + "❌ Connection lost to server")
            self.connected = False
            return None
        except json.JSONDecodeError:
            print(Fore.RED + "❌ Invalid response from server")
            return None
        except Exception as e:
            print(Fore.RED + f"❌ Communication error: {e}")
            return None

    def check_connection(self):
        """Check if still connected to server"""
        if not self.connected:
            print(Fore.RED + Back.RED + Fore.WHITE + " DISCONNECTED " + Style.RESET_ALL + 
                  Fore.RED + " Please restart the client.")
            return False
        return True

    def register_user(self):
        """Register a new user"""
        print("\n" + Fore.MAGENTA + "="*50)
        print(Fore.MAGENTA + "🆕 " + Back.MAGENTA + Fore.WHITE + " USER REGISTRATION " + Style.RESET_ALL)
        print(Fore.MAGENTA + "="*50)
        
        username = input(Fore.GREEN + "👤 Enter username: " + Fore.WHITE).strip()
        if not username:
            print(Fore.RED + "❌ Username cannot be empty")
            return False
            
        password = input(Fore.GREEN + "🔒 Enter password: " + Fore.WHITE).strip()
        if not password:
            print(Fore.RED + "❌ Password cannot be empty")
            return False
            
        email = input(Fore.GREEN + "📧 Enter email: " + Fore.WHITE).strip()
        address = input(Fore.GREEN + "🏠 Enter address: " + Fore.WHITE).strip()
        
        request = {
            'action': 'register',
            'username': username,
            'password': password,
            'email': email,
            'address': address
        }
        
        response = self.send_request(request)
        if response:
            if response['success']:
                print(Fore.GREEN + "✅ " + Back.GREEN + Fore.BLACK + " SUCCESS " + Style.RESET_ALL + 
                      Fore.GREEN + f" {response['message']}")
            else:
                print(Fore.RED + "❌ " + Back.RED + Fore.WHITE + " FAILED " + Style.RESET_ALL + 
                      Fore.RED + f" {response['message']}")
            return response['success']
        return False

    def login_user(self):
        """Login user"""
        print("\n" + Fore.BLUE + "="*50)
        print(Fore.BLUE + "🔐 " + Back.BLUE + Fore.WHITE + " USER LOGIN " + Style.RESET_ALL)
        print(Fore.BLUE + "="*50)
        
        username = input(Fore.CYAN + "👤 Enter username: " + Fore.WHITE).strip()
        password = input(Fore.CYAN + "🔒 Enter password: " + Fore.WHITE).strip()
        
        if not username or not password:
            print(Fore.RED + "❌ Username and password cannot be empty")
            return False
        
        request = {
            'action': 'login',
            'username': username,
            'password': password
        }
        
        self.animated_loading("🔐 Verifying credentials", 2)
        
        response = self.send_request(request)
        if response and response['success']:
            self.current_user = username
            
            # Success animation
            welcome_text = f"Welcome back, {username}! 🎉"
            print(Fore.GREEN + "✅ " + Back.GREEN + Fore.BLACK + " LOGIN SUCCESS " + Style.RESET_ALL)
            self.typewriter_effect(welcome_text, Fore.GREEN, 0.05)
            return True
        elif response:
            print(Fore.RED + "❌ " + Back.RED + Fore.WHITE + " LOGIN FAILED " + Style.RESET_ALL + 
                  Fore.RED + f" {response['message']}")
        return False

    def logout_user(self):
        """Logout current user"""
        if self.current_user:
            # Enhanced logout animation
            print(Fore.YELLOW + f"\n👋 Logging out {self.current_user}...")
            
            # Progress bar animation
            print(Fore.CYAN + "Progress: [", end="")
            for i in range(20):
                print(Fore.GREEN + "█", end="", flush=True)
                time.sleep(0.05)
            print(Fore.CYAN + "] 100%" + Style.RESET_ALL)

            request = {
                'action': 'logout',
                'username': self.current_user
            }

            response = self.send_request(request)
            if response and response['success']:
                print(Fore.GREEN + "✅ " + Back.GREEN + Fore.BLACK + " LOGGED OUT " + Style.RESET_ALL + 
                      Fore.GREEN + f" Goodbye, {self.current_user}!")
                self.current_user = None
                return True
            else:
                print(Fore.RED + "❌ Logout failed")
                return False
        else:
            print(Fore.YELLOW + "ℹ️  No user logged in")
            return False

    def view_products(self):
        """View available products"""
        print("\n" + Fore.MAGENTA + "="*70)
        print(Fore.MAGENTA + "🛍️  " + Back.MAGENTA + Fore.WHITE + " PRODUCT CATALOG " + Style.RESET_ALL)
        print(Fore.MAGENTA + "="*70)
        print(Fore.CYAN + "1. 📦 View all products")
        print(Fore.CYAN + "2. 🏷️  View by category")
        
        choice = input(Fore.YELLOW + "Choose option (1-2): " + Fore.WHITE).strip()
        
        request = {'action': 'get_products'}
        
        if choice == '2':
            print(Fore.CYAN + "\nAvailable categories: " + Fore.YELLOW + "Electronics, Home, Books, Stationery")
            category = input(Fore.GREEN + "Enter category: " + Fore.WHITE).strip()
            if category:
                request['category'] = category
        
        self.animated_loading("📡 Fetching products")
        response = self.send_request(request)
        if response and response['success']:
            products = response['products']
            if not products:
                print(Fore.YELLOW + "📭 No products found.")
                return
            
            print(f"\n{Fore.CYAN}{'ID':<5} {'Name':<25} {'Price':<10} {'Stock':<8} {'Category':<12} {'Description'}")
            print(Fore.CYAN + "-" * 80)
            
            for product_id, product in products.items():
                color = Fore.GREEN if product['stock'] > 10 else Fore.YELLOW if product['stock'] > 0 else Fore.RED
                print(f"{color}{product_id:<5} {product['name'][:24]:<25} ${product['price']:<9.2f} {product['stock']:<8} {product['category']:<12} {product['description'][:30]}")
                
        else:
            print(Fore.RED + "❌ Failed to retrieve products")

    def add_to_cart(self):
        """Add product to cart"""
        if not self.current_user:
            print(Fore.RED + "❌ Please login first")
            return
        
        print("\n" + Fore.GREEN + "="*50)
        print(Fore.GREEN + "🛒 " + Back.GREEN + Fore.BLACK + " ADD TO CART " + Style.RESET_ALL)
        print(Fore.GREEN + "="*50)
        
        try:
            product_id = int(input(Fore.CYAN + "📦 Enter product ID: " + Fore.WHITE).strip())
            quantity = int(input(Fore.CYAN + "🔢 Enter quantity: " + Fore.WHITE).strip())
            
            if quantity <= 0:
                print(Fore.RED + "❌ Quantity must be positive")
                return
                
        except ValueError:
            print(Fore.RED + "❌ Please enter valid numbers")
            return
        
        request = {
            'action': 'add_to_cart',
            'username': self.current_user,
            'product_id': product_id,
            'quantity': quantity
        }
        
        self.animated_loading("🛒 Adding to cart")
        response = self.send_request(request)
        if response:
            if response['success']:
                print(Fore.GREEN + "✅ " + Back.GREEN + Fore.BLACK + " ADDED " + Style.RESET_ALL + 
                      Fore.GREEN + f" {response['message']}")
            else:
                print(Fore.RED + "❌ " + Back.RED + Fore.WHITE + " FAILED " + Style.RESET_ALL + 
                      Fore.RED + f" {response['message']}")

    def view_cart(self):
        """View shopping cart"""
        if not self.current_user:
            print(Fore.RED + "❌ Please login first")
            return
        
        request = {
            'action': 'view_cart',
            'username': self.current_user
        }
        
        self.animated_loading("🛒 Loading your cart")
        response = self.send_request(request)
        if response and response['success']:
            cart = response['cart']
            
            if not cart['items']:
                print(Fore.YELLOW + "\n🛒 Your cart is empty")
                return
            
            print("\n" + Fore.BLUE + "="*70)
            print(Fore.BLUE + "🛒 " + Back.BLUE + Fore.WHITE + " YOUR SHOPPING CART " + Style.RESET_ALL)
            print(Fore.BLUE + "="*70)
            print(f"{Fore.CYAN}{'ID':<5} {'Name':<25} {'Price':<10} {'Qty':<5} {'Subtotal'}")
            print(Fore.CYAN + "-" * 55)
            
            for product_id, item in cart['items'].items():
                print(f"{Fore.WHITE}{product_id:<5} {item['name'][:24]:<25} ${item['price']:<9.2f} {item['quantity']:<5} {Fore.GREEN}${item['subtotal']:.2f}")
            
            print(Fore.CYAN + "-" * 55)
            print(f"{Fore.YELLOW}{'TOTAL':<45} {Back.YELLOW + Fore.BLACK} ${cart['total']:.2f} {Style.RESET_ALL}")
            print(Fore.BLUE + "="*70)
        else:
            print(Fore.RED + "❌ Failed to retrieve cart")

    def place_order(self):
        """Place order"""
        if not self.current_user:
            print(Fore.RED + "❌ Please login first")
            return
        
        print("\n" + Fore.YELLOW + "="*50)
        print(Fore.YELLOW + "📋 " + Back.YELLOW + Fore.BLACK + " PLACE ORDER " + Style.RESET_ALL)
        print(Fore.YELLOW + "="*50)
        
        # First show current cart
        self.view_cart()
        
        confirm = input(Fore.GREEN + "\n✅ Confirm order? (y/n): " + Fore.WHITE).strip().lower()
        if confirm != 'y':
            print(Fore.YELLOW + "❌ Order cancelled")
            return
        
        request = {
            'action': 'place_order',
            'username': self.current_user
        }
        
        self.animated_loading("📦 Processing your order", 3)
        response = self.send_request(request)
        if response:
            if response['success']:
                print(Fore.GREEN + "✅ " + Back.GREEN + Fore.BLACK + " ORDER PLACED " + Style.RESET_ALL)
                self.typewriter_effect(f"🎉 {response['message']}", Fore.GREEN, 0.03)
            else:
                print(Fore.RED + "❌ " + Back.RED + Fore.WHITE + " ORDER FAILED " + Style.RESET_ALL + 
                      Fore.RED + f" {response['message']}")

    def view_order_history(self):
        """View order history"""
        if not self.current_user:
            print(Fore.RED + "❌ Please login first")
            return
        
        request = {
            'action': 'get_orders',
            'username': self.current_user
        }
        
        self.animated_loading("📋 Loading order history")
        response = self.send_request(request)
        if response and response['success']:
            orders = response['orders']
            
            if not orders:
                print(Fore.YELLOW + "\n📭 No orders found")
                return
            
            print("\n" + Fore.MAGENTA + "="*80)
            print(Fore.MAGENTA + "📋 " + Back.MAGENTA + Fore.WHITE + " ORDER HISTORY " + Style.RESET_ALL)
            print(Fore.MAGENTA + "="*80)
            
            for order_id, order in orders.items():
                print(f"\n{Fore.CYAN}🛍️  Order #{order_id}")
                print(f"{Fore.WHITE}   Date: {Fore.YELLOW}{order['timestamp']}")
                print(f"{Fore.WHITE}   Status: {Back.GREEN + Fore.BLACK if order['status'] == 'Confirmed' else Back.YELLOW + Fore.BLACK} {order['status']} {Style.RESET_ALL}")
                print(f"{Fore.WHITE}   Total: {Fore.GREEN}${order['total']:.2f}")
                print(f"{Fore.WHITE}   Items:")
                
                for item_id, item in order['items'].items():
                    print(f"{Fore.CYAN}     - {item['name']} x{item['quantity']} @ ${item['price']:.2f} = {Fore.GREEN}${item['subtotal']:.2f}")
                print(Fore.CYAN + "-" * 60)
        else:
            print(Fore.RED + "❌ Failed to retrieve order history")

    def server_status(self):
        """Check server status"""
        request = {'action': 'server_status'}
        
        self.animated_loading("🖥️  Checking server status")
        response = self.send_request(request)
        if response and response['success']:
            print("\n" + Fore.GREEN + "="*50)
            print(Fore.GREEN + "🖥️  " + Back.GREEN + Fore.BLACK + " SERVER STATUS " + Style.RESET_ALL)
            print(Fore.GREEN + "="*50)
            print(f"{Fore.CYAN}Status: {Fore.GREEN}{response['status']}")
            print(f"{Fore.CYAN}Active Users: {Fore.YELLOW}{response['active_users']}")
            print(f"{Fore.CYAN}Server Time: {Fore.WHITE}{response['server_time']}")
            print(Fore.GREEN + "="*50)
        else:
            print(Fore.RED + "❌ Failed to get server status")

    def display_main_menu(self):
        """Display main menu with enhanced colors"""
        print("\n" + Fore.CYAN + "="*60)
        print(Fore.CYAN + "🛒 " + Back.CYAN + Fore.BLACK + " SHOPPING MART - MAIN MENU " + Style.RESET_ALL)
        print(Fore.CYAN + "="*60)
        
        if self.current_user:
            print(f"{Fore.GREEN}👤 Logged in as: {Back.GREEN + Fore.BLACK} {self.current_user} {Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}📋 SHOPPING OPTIONS:")
            print(f"{Fore.WHITE}1. {Fore.MAGENTA}🛍️  View Products")
            print(f"{Fore.WHITE}2. {Fore.GREEN}➕ Add to Cart")
            print(f"{Fore.WHITE}3. {Fore.BLUE}🛒 View Cart")
            print(f"{Fore.WHITE}4. {Fore.YELLOW}📦 Place Order")
            print(f"{Fore.WHITE}5. {Fore.CYAN}📋 Order History")
            print(f"{Fore.WHITE}6. {Fore.RED}👋 Logout")
            print(f"\n{Fore.CYAN}🔧 SYSTEM OPTIONS:")
            print(f"{Fore.WHITE}7. {Fore.GREEN}🖥️  Server Status")
            print(f"{Fore.WHITE}8. {Fore.RED}🚪 Exit")
        else:
            print(f"{Fore.RED}👤 Not logged in")
            print(f"\n{Fore.BLUE}🔐 AUTHENTICATION:")
            print(f"{Fore.WHITE}1. {Fore.BLUE}🔐 Login")
            print(f"{Fore.WHITE}2. {Fore.MAGENTA}🆕 Register")
            print(f"{Fore.WHITE}3. {Fore.CYAN}🛍️  View Products (Guest)")
            print(f"\n{Fore.CYAN}🔧 SYSTEM OPTIONS:")
            print(f"{Fore.WHITE}4. {Fore.GREEN}🖥️  Server Status")
            print(f"{Fore.WHITE}5. {Fore.RED}🚪 Exit")
        
        print(Fore.CYAN + "="*60)

    def handle_logged_in_menu(self):
        """Handle menu for logged-in users"""
        while True:
            if not self.check_connection():
                break
                
            self.display_main_menu()
            choice = input(Fore.YELLOW + "👉 Choose option: " + Fore.WHITE).strip()
            
            if choice == '1':
                self.view_products()
            elif choice == '2':
                self.add_to_cart()
            elif choice == '3':
                self.view_cart()
            elif choice == '4':
                self.place_order()
            elif choice == '5':
                self.view_order_history()
            elif choice == '6':
                if self.logout_user():
                    break  # Exit to guest menu after successful logout
            elif choice == '7':
                self.server_status()
            elif choice == '8':
                print(Fore.YELLOW + "👋 Goodbye!")
                return True  # Exit application
            else:
                print(Fore.RED + "❌ Invalid choice. Please try again.")
            
            if choice != '8':
                input(Fore.CYAN + "\n📋 Press Enter to continue..." + Fore.WHITE)
        
        return False  # Return to guest menu

    def handle_guest_menu(self):
        """Handle menu for guests (not logged in)"""
        while True:
            if not self.check_connection():
                break
                
            self.display_main_menu()
            choice = input(Fore.YELLOW + "👉 Choose option: " + Fore.WHITE).strip()
            
            if choice == '1':
                if self.login_user():
                    # After successful login, switch to logged-in menu
                    if self.handle_logged_in_menu():
                        break  # Exit application
                    # If returned False, continue with guest menu
            elif choice == '2':
                self.register_user()
            elif choice == '3':
                self.view_products()
            elif choice == '4':
                self.server_status()
            elif choice == '5':
                print(Fore.YELLOW + "👋 Goodbye!")
                break
            else:
                print(Fore.RED + "❌ Invalid choice. Please try again.")
            
            if choice in ['2', '3', '4']:
                input(Fore.CYAN + "\n📋 Press Enter to continue..." + Fore.WHITE)

    def print_client_info(self):
        """Print client startup information with enhanced styling"""
        print("\n" + Fore.CYAN + "="*70)
        print(Fore.CYAN + "🛒 " + Back.CYAN + Fore.BLACK + " SHOPPING MART CLIENT " + Style.RESET_ALL)
        print(Fore.CYAN + "="*70)
        print(f"{Fore.YELLOW}Server: {Fore.WHITE}{self.host}:{self.port}")
        print(f"{Fore.YELLOW}Client started at: {Fore.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n{Fore.GREEN}Features:")
        print(f"{Fore.WHITE}  ✓ User registration and authentication")
        print(f"{Fore.WHITE}  ✓ Product browsing and search")
        print(f"{Fore.WHITE}  ✓ Shopping cart management")
        print(f"{Fore.WHITE}  ✓ Order placement and history")
        print(f"{Fore.WHITE}  ✓ Real-time server communication")
        print(f"{Fore.WHITE}  ✓ Enhanced UI with colors and animations")
        print(Fore.CYAN + "="*70)

    def run(self):
        """Main client loop"""
        self.print_client_info()
        
        if not self.connect_to_server():
            print(Fore.RED + "❌ Cannot start client without server connection")
            return
        
        try:
            print(Fore.GREEN + "\n🚀 " + Back.GREEN + Fore.BLACK + " CLIENT STARTED " + Style.RESET_ALL + 
                  Fore.GREEN + " Successfully!")
            self.handle_guest_menu()
            
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n🛑 Client shutting down...")
        except Exception as e:
            print(Fore.RED + f"\n❌ Unexpected error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.current_user:
            self.logout_user()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print(Fore.GREEN + "✅ Client stopped successfully")

def print_usage():
    """Print usage instructions"""
    print("\n" + Fore.CYAN + "="*70)
    print(Fore.CYAN + "🛒 Shopping Mart Client - Usage Instructions")
    print(Fore.CYAN + "="*70)
    print(f"{Fore.YELLOW}Usage: {Fore.WHITE}python shopping_client.py [host] [port]")
    print(f"\n{Fore.GREEN}Examples:")
    print(f"{Fore.WHITE}  python shopping_client.py                    # Connect to localhost:8888")
    print(f"{Fore.WHITE}  python shopping_client.py localhost 8888     # Connect to localhost:8888")
    print(f"{Fore.WHITE}  python shopping_client.py 192.168.1.100 8888 # Connect to remote server")
    print(f"\n{Fore.YELLOW}Default values:")
    print(f"{Fore.WHITE}  Host: localhost")
    print(f"{Fore.WHITE}  Port: 8888")
    print(Fore.CYAN + "="*70)

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) == 1:
        # Default connection
        host = 'localhost'
        port = 8888
    elif len(sys.argv) == 2:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print_usage()
            sys.exit(0)
        host = sys.argv[1]
        port = 8888
    elif len(sys.argv) == 3:
        host = sys.argv[1]
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(Fore.RED + "❌ Invalid port number")
            print_usage()
            sys.exit(1)
    else:
        print(Fore.RED + "❌ Too many arguments")
        print_usage()
        sys.exit(1)
    
    # Validate port range
    if not (1 <= port <= 65535):
        print(Fore.RED + "❌ Port must be between 1 and 65535")
        sys.exit(1)
    
    # Create and run client
    client = ShoppingMartClient(host, port)
    client.run()