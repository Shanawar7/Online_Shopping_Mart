import socket
import threading
import json
import hashlib
import sqlite3
import time
from datetime import datetime
import sys
import os

class ShoppingMartServer:
    def __init__(self, host='0.0.0.0', port=8, db_name='shopping_mart.db'):
        self.host = host  # 0.0.0.0 allows connections from any IP
        self.port = port
        self.db_name = db_name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Database lock for thread safety
        self.db_lock = threading.Lock()
        
        # Connected clients tracking
        self.connected_clients = {}
        self.client_counter = 0
        
        # Initialize database
        self.init_database()

    def get_server_ip(self):
        """Get the server's IP address for client connections"""
        try:
            # Connect to a remote server to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except:
            return "localhost"

    def get_db_connection(self):
        """Get database connection with thread safety"""
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def init_database(self):
        """Initialize database tables and sample data"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT NOT NULL,
                    address TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create cart_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cart_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    UNIQUE(username, product_id)
                )
            ''')
            
            # Create orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'Confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create order_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Create active_sessions table for tracking connected clients
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    client_ip TEXT NOT NULL,
                    client_port INTEGER NOT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
            # Check if products exist, if not insert sample data
            cursor.execute('SELECT COUNT(*) FROM products')
            if cursor.fetchone()[0] == 0:
                self.insert_sample_products(cursor)
                conn.commit()
            
            conn.close()

    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT password_hash FROM users WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result['password_hash'] == self.hash_password(password)
            return False

    def log_user_session(self, username, client_ip, client_port):
        """Log user session for tracking"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Remove any existing sessions for this user
                cursor.execute('''
                    DELETE FROM active_sessions WHERE username = ?
                ''', (username,))
                
                # Add new session
                cursor.execute('''
                    INSERT INTO active_sessions (username, client_ip, client_port)
                    VALUES (?, ?, ?)
                ''', (username, client_ip, client_port))
                
                conn.commit()
            except Exception as e:
                print(f"Error logging session: {e}")
            finally:
                conn.close()

    def remove_user_session(self, username):
        """Remove user session on logout"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    DELETE FROM active_sessions WHERE username = ?
                ''', (username,))
                conn.commit()
            except Exception as e:
                print(f"Error removing session: {e}")
            finally:
                conn.close()

    def get_active_users(self):
        """Get count of active users"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM active_sessions')
            count = cursor.fetchone()[0]
            conn.close()
            return count

    def register_user(self, username, password, email, address):
        """Register a new user"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, address)
                    VALUES (?, ?, ?, ?)
                ''', (username, self.hash_password(password), email, address))
                
                conn.commit()
                conn.close()
                return True, "Registration successful"
            
            except sqlite3.IntegrityError:
                conn.close()
                return False, "Username already exists"
            except Exception as e:
                conn.close()
                return False, f"Registration failed: {str(e)}"

    def get_products(self, category=None):
        """Get all products or products by category"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM products WHERE LOWER(category) = LOWER(?) AND stock > 0
                    ORDER BY name
                ''', (category,))
            else:
                cursor.execute('''
                    SELECT * FROM products WHERE stock > 0 ORDER BY category, name
                ''')
            
            products = {}
            for row in cursor.fetchall():
                products[row['id']] = {
                    'name': row['name'],
                    'price': row['price'],
                    'stock': row['stock'],
                    'category': row['category'],
                    'description': row['description']
                }
            
            conn.close()
            return products

    def add_to_cart(self, username, product_id, quantity):
        """Add product to user's cart"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Check if product exists and has sufficient stock
                cursor.execute('''
                    SELECT stock FROM products WHERE id = ?
                ''', (product_id,))
                
                result = cursor.fetchone()
                if not result:
                    conn.close()
                    return False, "Product not found"
                
                if result['stock'] < quantity:
                    conn.close()
                    return False, "Insufficient stock"
                
                # Check if item already in cart
                cursor.execute('''
                    SELECT quantity FROM cart_items WHERE username = ? AND product_id = ?
                ''', (username, product_id))
                
                existing_item = cursor.fetchone()
                
                if existing_item:
                    # Update existing cart item
                    new_quantity = existing_item['quantity'] + quantity
                    cursor.execute('''
                        UPDATE cart_items SET quantity = ? WHERE username = ? AND product_id = ?
                    ''', (new_quantity, username, product_id))
                else:
                    # Add new cart item
                    cursor.execute('''
                        INSERT INTO cart_items (username, product_id, quantity)
                        VALUES (?, ?, ?)
                    ''', (username, product_id, quantity))
                
                conn.commit()
                conn.close()
                return True, "Product added to cart"
                
            except Exception as e:
                conn.close()
                return False, f"Error adding to cart: {str(e)}"

    def view_cart(self, username):
        """View user's cart"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT c.product_id, c.quantity, p.name, p.price
                FROM cart_items c
                JOIN products p ON c.product_id = p.id
                WHERE c.username = ?
            ''', (username,))
            
            cart_items = cursor.fetchall()
            conn.close()
            
            if not cart_items:
                return {'items': {}, 'total': 0}
            
            cart_details = {}
            total = 0
            
            for item in cart_items:
                subtotal = item['price'] * item['quantity']
                cart_details[item['product_id']] = {
                    'name': item['name'],
                    'price': item['price'],
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                }
                total += subtotal
            
            return {'items': cart_details, 'total': total}

    def place_order(self, username):
        """Place order from user's cart"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Get cart items
                cursor.execute('''
                    SELECT c.product_id, c.quantity, p.name, p.price, p.stock
                    FROM cart_items c
                    JOIN products p ON c.product_id = p.id
                    WHERE c.username = ?
                ''', (username,))
                
                cart_items = cursor.fetchall()
                
                if not cart_items:
                    conn.close()
                    return False, "Cart is empty"
                
                # Check stock availability
                for item in cart_items:
                    if item['stock'] < item['quantity']:
                        conn.close()
                        return False, f"Insufficient stock for {item['name']}"
                
                # Calculate total
                total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
                
                # Create order
                cursor.execute('''
                    INSERT INTO orders (username, total_amount)
                    VALUES (?, ?)
                ''', (username, total_amount))
                
                order_id = cursor.lastrowid
                
                # Add order items and update stock
                for item in cart_items:
                    subtotal = item['price'] * item['quantity']
                    
                    # Add order item
                    cursor.execute('''
                        INSERT INTO order_items (order_id, product_id, product_name, price, quantity, subtotal)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (order_id, item['product_id'], item['name'], item['price'], item['quantity'], subtotal))
                    
                    # Update product stock
                    cursor.execute('''
                        UPDATE products SET stock = stock - ? WHERE id = ?
                    ''', (item['quantity'], item['product_id']))
                
                # Clear cart
                cursor.execute('''
                    DELETE FROM cart_items WHERE username = ?
                ''', (username,))
                
                conn.commit()
                conn.close()
                
                return True, f"Order #{order_id} placed successfully. Total: ${total_amount:.2f}"
                
            except Exception as e:
                conn.rollback()
                conn.close()
                return False, f"Error placing order: {str(e)}"

    def get_user_orders(self, username):
        """Get user's order history"""
        with self.db_lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get orders
            cursor.execute('''
                SELECT * FROM orders WHERE username = ? ORDER BY created_at DESC
            ''', (username,))
            
            orders = cursor.fetchall()
            user_orders = {}
            
            for order in orders:
                order_id = order['id']
                
                # Get order items
                cursor.execute('''
                    SELECT * FROM order_items WHERE order_id = ?
                ''', (order_id,))
                
                order_items = cursor.fetchall()
                items_dict = {}
                
                for item in order_items:
                    items_dict[item['product_id']] = {
                        'name': item['product_name'],
                        'price': item['price'],
                        'quantity': item['quantity'],
                        'subtotal': item['subtotal']
                    }
                
                user_orders[order_id] = {
                    'user': order['username'],
                    'items': items_dict,
                    'total': order['total_amount'],
                    'timestamp': order['created_at'],
                    'status': order['status']
                }
            
            conn.close()
            return user_orders

    def handle_client_request(self, request_data, client_address):
        """Handle client requests"""
        try:
            request = json.loads(request_data)
            action = request.get('action')
            
            if action == 'register':
                success, message = self.register_user(
                    request['username'], request['password'],
                    request['email'], request['address']
                )
                return {'success': success, 'message': message}
            
            elif action == 'login':
                success = self.authenticate_user(request['username'], request['password'])
                if success:
                    self.log_user_session(request['username'], client_address[0], client_address[1])
                return {'success': success, 'message': 'Login successful' if success else 'Invalid credentials'}
            
            elif action == 'logout':
                self.remove_user_session(request['username'])
                return {'success': True, 'message': 'Logged out successfully'}
            
            elif action == 'get_products':
                category = request.get('category')
                products = self.get_products(category)
                return {'success': True, 'products': products}
            
            elif action == 'add_to_cart':
                success, message = self.add_to_cart(
                    request['username'], request['product_id'], request['quantity']
                )
                return {'success': success, 'message': message}
            
            elif action == 'view_cart':
                cart = self.view_cart(request['username'])
                return {'success': True, 'cart': cart}
            
            elif action == 'place_order':
                success, message = self.place_order(request['username'])
                return {'success': success, 'message': message}
            
            elif action == 'get_orders':
                orders = self.get_user_orders(request['username'])
                return {'success': True, 'orders': orders}
            
            elif action == 'server_status':
                active_users = self.get_active_users()
                return {
                    'success': True, 
                    'status': 'Server running',
                    'active_users': active_users,
                    'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            else:
                return {'success': False, 'message': 'Invalid action'}
        
        except json.JSONDecodeError:
            return {'success': False, 'message': 'Invalid JSON format'}
        except Exception as e:
            return {'success': False, 'message': f'Server error: {str(e)}'}

    def handle_client(self, client_socket, client_address):
        """Handle individual client connections"""
        client_id = self.client_counter
        self.client_counter += 1
        self.connected_clients[client_id] = {
            'socket': client_socket,
            'address': client_address,
            'connected_at': datetime.now()
        }
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Client #{client_id} connected from {client_address}")
        
        try:
            while True:
                # Set timeout for socket operations
                client_socket.settimeout(300)  # 5 minutes timeout
                
                # Receive data from client
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Client #{client_id} ({client_address[0]}): {data[:100]}...")
                
                # Process request
                response = self.handle_client_request(data, client_address)
                
                # Send response
                response_json = json.dumps(response)
                client_socket.send(response_json.encode('utf-8'))
                
        except socket.timeout:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Client #{client_id} timed out")
        except ConnectionResetError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Client #{client_id} disconnected unexpectedly")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error handling client #{client_id}: {e}")
        finally:
            client_socket.close()
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Client #{client_id} disconnected")

    def print_server_info(self):
        """Print server connection information"""
        server_ip = self.get_server_ip()
        print("\n" + "="*60)
        print("🛒 SHOPPING MART SERVER STARTED")
        print("="*60)
        print(f"Server Host: {self.host}")
        print(f"Server Port: {self.port}")
        print(f"Local IP: {server_ip}")
        print(f"Database: {self.db_name}")
        print("\nConnection Instructions for Clients:")
        print(f"  - Same machine: python shopping_client.py localhost {self.port}")
        print(f"  - Other machines: python shopping_client.py {server_ip} {self.port}")
        print("\nFeatures:")
        print("  ✓ Multi-client support with threading")
        print("  ✓ Network connections from other machines")
        print("  ✓ Session tracking and user management")
        print("  ✓ Thread-safe database operations")
        print("="*60)
        print("Waiting for client connections...")
        print("Press Ctrl+C to stop the server")
        print("="*60 + "\n")

    def start_server(self):
        """Start the server"""
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)  # Increased backlog for more concurrent connections
            
            self.print_server_info()
            
            while True:
                try:
                    client_socket, client_address = self.socket.accept()
                    
                    # Create a new thread for each client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        name=f"Client-{client_address[0]}:{client_address[1]}"
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    continue
                
        except KeyboardInterrupt:
            print("\n\n🛑 Server shutting down...")
            print(f"Total clients served: {self.client_counter}")
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            # Close all client connections
            for client_info in self.connected_clients.values():
                try:
                    client_info['socket'].close()
                except:
                    pass
            
            self.socket.close()
            print("✅ Server stopped successfully")

if __name__ == "__main__":
    # Allow custom host and port via command line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8888
    
    server = ShoppingMartServer(host, port)
    server.start_server()