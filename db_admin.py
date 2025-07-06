import sqlite3
import sys
import time
from datetime import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

class DatabaseAdmin:
    def __init__(self, db_name='shopping_mart.db'):
        self.db_name = db_name
        
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def animate_loading(self, text="Loading", duration=1.5):
        """Show animated loading spinner"""
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        end_time = time.time() + duration
        
        while time.time() < end_time:
            for char in chars:
                print(f"\r{Fore.CYAN}{char} {text}...", end="", flush=True)
                time.sleep(0.1)
        print(f"\r{Fore.GREEN}✓ {text} complete!{' ' * 20}")
        time.sleep(0.3)
    
    def print_header(self, title):
        """Print a colorful header"""
        width = max(60, len(title) + 20)
        border = "=" * width
        
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{border}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{title:^{width}}")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{border}")
    
    def print_success(self, message):
        """Print success message with animation"""
        print(f"{Fore.GREEN}{Style.BRIGHT}✓ {message}")
    
    def print_error(self, message):
        """Print error message with color"""
        print(f"{Fore.RED}{Style.BRIGHT}✗ {message}")
    
    def print_info(self, message):
        """Print info message with color"""
        print(f"{Fore.CYAN}{Style.BRIGHT}ℹ {message}")
    
    def show_users(self):
        """Display all users with colors"""
        self.print_header("USER MANAGEMENT")
        self.animate_loading("Fetching users")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        
        if not users:
            self.print_info("No users found.")
            conn.close()
            return
        
        # Header with colors
        print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT}{'ID':<5} {'Username':<15} {'Email':<25} {'Address':<30} {'Created':<20}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'-' * 100}")
        
        for i, user in enumerate(users):
            color = Fore.GREEN if i % 2 == 0 else Fore.WHITE
            print(f"{color}{user['id']:<5} {user['username']:<15} {user['email']:<25} {user['address']:<30} {user['created_at']:<20}")
        
        print(f"{Fore.YELLOW}{Style.BRIGHT}\nTotal users: {len(users)}")
        conn.close()
    
    def show_products(self):
        """Display all products with colors"""
        self.print_header("PRODUCT INVENTORY")
        self.animate_loading("Loading products")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products ORDER BY category, name')
        products = cursor.fetchall()
        
        if not products:
            self.print_info("No products found.")
            conn.close()
            return
        
        # Header with colors
        print(f"\n{Back.GREEN}{Fore.WHITE}{Style.BRIGHT}{'ID':<5} {'Name':<25} {'Price':<10} {'Stock':<8} {'Category':<12} {'Description':<25}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'-' * 95}")
        
        for i, product in enumerate(products):
            desc = product['description'][:22] + "..." if len(product['description']) > 22 else product['description']
            
            # Color code based on stock level
            if product['stock'] == 0:
                stock_color = Fore.RED + Style.BRIGHT
            elif product['stock'] < 10:
                stock_color = Fore.YELLOW
            else:
                stock_color = Fore.GREEN
            
            row_color = Fore.CYAN if i % 2 == 0 else Fore.WHITE
            
            print(f"{row_color}{product['id']:<5} {product['name']:<25} {Fore.GREEN}${product['price']:<9.2f} "
                  f"{stock_color}{product['stock']:<8} {row_color}{product['category']:<12} {desc}")
        
        print(f"{Fore.YELLOW}{Style.BRIGHT}\nTotal products: {len(products)}")
        conn.close()
    
    def show_orders(self):
        """Display all orders with colors"""
        self.print_header("ORDER MANAGEMENT")
        self.animate_loading("Fetching orders")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
        orders = cursor.fetchall()
        
        if not orders:
            self.print_info("No orders found.")
            conn.close()
            return
        
        # Header with colors
        print(f"\n{Back.MAGENTA}{Fore.WHITE}{Style.BRIGHT}{'Order ID':<10} {'Username':<15} {'Total':<12} {'Status':<12} {'Date':<20}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'-' * 75}")
        
        for i, order in enumerate(orders):
            # Color code based on status
            if order['status'] == 'completed':
                status_color = Fore.GREEN + Style.BRIGHT
            elif order['status'] == 'pending':
                status_color = Fore.YELLOW
            else:
                status_color = Fore.RED
            
            row_color = Fore.LIGHTBLUE_EX if i % 2 == 0 else Fore.WHITE
            
            print(f"{row_color}{order['id']:<10} {order['username']:<15} {Fore.GREEN}${order['total_amount']:<11.2f} "
                  f"{status_color}{order['status']:<12} {row_color}{order['created_at']}")
        
        print(f"{Fore.YELLOW}{Style.BRIGHT}\nTotal orders: {len(orders)}")
        conn.close()
    
    def show_order_details(self, order_id):
        """Show detailed order information with colors"""
        self.print_header(f"ORDER #{order_id} DETAILS")
        self.animate_loading("Loading order details")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get order info
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            self.print_error(f"Order {order_id} not found.")
            conn.close()
            return
        
        # Order summary with colors
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Customer: {Fore.WHITE}{order['username']}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Total: {Fore.GREEN}${order['total_amount']:.2f}")
        
        # Status with color coding
        if order['status'] == 'completed':
            status_color = Fore.GREEN + Style.BRIGHT
        elif order['status'] == 'pending':
            status_color = Fore.YELLOW
        else:
            status_color = Fore.RED
        
        print(f"{Fore.CYAN}{Style.BRIGHT}Status: {status_color}{order['status'].upper()}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Date: {Fore.WHITE}{order['created_at']}")
        
        # Get order items
        cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,))
        items = cursor.fetchall()
        
        if items:
            print(f"\n{Back.YELLOW}{Fore.BLACK}{Style.BRIGHT}{'Product':<25} {'Price':<10} {'Qty':<5} {'Subtotal':<12}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'-' * 55}")
            
            for i, item in enumerate(items):
                row_color = Fore.LIGHTGREEN_EX if i % 2 == 0 else Fore.WHITE
                print(f"{row_color}{item['product_name']:<25} {Fore.GREEN}${item['price']:<9.2f} "
                      f"{row_color}{item['quantity']:<5} {Fore.GREEN}${item['subtotal']:.2f}")
        
        conn.close()
    
    def show_cart_contents(self):
        """Show all current cart contents with colors"""
        self.print_header("SHOPPING CARTS")
        self.animate_loading("Loading cart contents")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.username, c.quantity, p.name, p.price
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            ORDER BY c.username, p.name
        ''')
        
        cart_items = cursor.fetchall()
        
        if not cart_items:
            self.print_info("No items in any carts.")
            conn.close()
            return
        
        print(f"\n{Back.CYAN}{Fore.WHITE}{Style.BRIGHT}{'Username':<15} {'Product':<25} {'Price':<10} {'Quantity':<8} {'Subtotal':<12}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 78}")
        
        current_user = None
        user_total = 0
        
        for i, item in enumerate(cart_items):
            if current_user != item['username']:
                if current_user:
                    print(f"{Fore.YELLOW}{Style.BRIGHT}{'Total for ' + current_user + ':':<58} ${user_total:.2f}")
                    print(f"{Fore.CYAN}{'-' * 78}")
                current_user = item['username']
                user_total = 0
            
            subtotal = item['price'] * item['quantity']
            user_total += subtotal
            
            row_color = Fore.LIGHTCYAN_EX if i % 2 == 0 else Fore.WHITE
            
            print(f"{row_color}{item['username']:<15} {item['name']:<25} {Fore.GREEN}${item['price']:<9.2f} "
                  f"{row_color}{item['quantity']:<8} {Fore.GREEN}${subtotal:.2f}")
        
        if current_user:
            print(f"{Fore.YELLOW}{Style.BRIGHT}{'Total for ' + current_user + ':':<58} ${user_total:.2f}")
        
        conn.close()
    
    def add_product(self):
        """Add a new product with colorful interface"""
        self.print_header("ADD NEW PRODUCT")
        
        print(f"{Fore.CYAN}Please enter product details:")
        name = input(f"{Fore.YELLOW}Product name: {Fore.WHITE}")
        
        try:
            price = float(input(f"{Fore.YELLOW}Price: {Fore.GREEN}${Fore.WHITE}"))
            stock = int(input(f"{Fore.YELLOW}Stock quantity: {Fore.WHITE}"))
        except ValueError:
            self.print_error("Invalid price or stock quantity.")
            return
        
        category = input(f"{Fore.YELLOW}Category: {Fore.WHITE}")
        description = input(f"{Fore.YELLOW}Description: {Fore.WHITE}")
        
        self.animate_loading("Adding product")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO products (name, price, stock, category, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, price, stock, category, description))
            
            conn.commit()
            self.print_success(f"Product '{name}' added successfully!")
        except Exception as e:
            self.print_error(f"Error adding product: {e}")
        finally:
            conn.close()
    
    def update_stock(self):
        """Update product stock with colorful interface"""
        self.print_header("UPDATE PRODUCT STOCK")
        
        try:
            product_id = int(input(f"{Fore.YELLOW}Product ID: {Fore.WHITE}"))
            new_stock = int(input(f"{Fore.YELLOW}New stock quantity: {Fore.WHITE}"))
        except ValueError:
            self.print_error("Invalid input.")
            return
        
        self.animate_loading("Updating stock")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                self.print_success(f"Stock updated successfully for product ID {product_id}")
            else:
                self.print_error(f"Product ID {product_id} not found.")
        except Exception as e:
            self.print_error(f"Error updating stock: {e}")
        finally:
            conn.close()
    
    def show_database_stats(self):
        """Show database statistics with colorful display"""
        self.print_header("DATABASE STATISTICS")
        self.animate_loading("Calculating statistics")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Count statistics
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM products')
        product_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM orders')
        order_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM cart_items')
        cart_items_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_amount) FROM orders')
        total_revenue = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(stock) FROM products')
        total_inventory = cursor.fetchone()[0] or 0
        
        # Display stats with colors and icons
        print(f"\n{Fore.CYAN}{Style.BRIGHT}👥 Total Users: {Fore.GREEN}{user_count}")
        print(f"{Fore.CYAN}{Style.BRIGHT}📦 Total Products: {Fore.GREEN}{product_count}")
        print(f"{Fore.CYAN}{Style.BRIGHT}🛒 Total Orders: {Fore.GREEN}{order_count}")
        print(f"{Fore.CYAN}{Style.BRIGHT}🛍️  Items in Carts: {Fore.YELLOW}{cart_items_count}")
        print(f"{Fore.CYAN}{Style.BRIGHT}💰 Total Revenue: {Fore.GREEN}${total_revenue:.2f}")
        print(f"{Fore.CYAN}{Style.BRIGHT}📊 Total Inventory: {Fore.BLUE}{total_inventory} items")
        
        conn.close()
    
    def main_menu(self):
        """Display colorful admin menu with animations"""
        while True:
            # Clear screen effect
            print("\n" * 2)
            
            # Animated title
            title = "🛒 SHOPPING MART DATABASE ADMIN 🛒"
            print(f"{Fore.MAGENTA}{Style.BRIGHT}{'=' * 60}")
            print(f"{Fore.YELLOW}{Style.BRIGHT}{title:^60}")
            print(f"{Fore.MAGENTA}{Style.BRIGHT}{'=' * 60}")
            print(f"{Fore.CYAN}Database: {Fore.WHITE}{Style.BRIGHT}{self.db_name}")
            
            # Menu options with colors and icons
            menu_options = [
                ("1", "👥", "Show Users", Fore.LIGHTBLUE_EX),
                ("2", "📦", "Show Products", Fore.LIGHTGREEN_EX),
                ("3", "🛒", "Show Orders", Fore.LIGHTYELLOW_EX),
                ("4", "📋", "Show Order Details", Fore.LIGHTMAGENTA_EX),
                ("5", "🛍️", "Show Cart Contents", Fore.LIGHTCYAN_EX),
                ("6", "➕", "Add Product", Fore.GREEN),
                ("7", "📊", "Update Stock", Fore.YELLOW),
                ("8", "📈", "Database Statistics", Fore.BLUE),
                ("9", "🚪", "Exit", Fore.RED)
            ]
            
            print(f"\n{Fore.WHITE}{Style.BRIGHT}Choose an option:")
            for num, icon, desc, color in menu_options:
                print(f"{color}{Style.BRIGHT}{num}. {icon} {desc}")
            
            choice = input(f"\n{Fore.CYAN}{Style.BRIGHT}Enter your choice (1-9): {Fore.WHITE}")
            
            if choice == '1':
                self.show_users()
            elif choice == '2':
                self.show_products()
            elif choice == '3':
                self.show_orders()
            elif choice == '4':
                try:
                    order_id = int(input(f"{Fore.YELLOW}Enter Order ID: {Fore.WHITE}"))
                    self.show_order_details(order_id)
                except ValueError:
                    self.print_error("Invalid Order ID.")
            elif choice == '5':
                self.show_cart_contents()
            elif choice == '6':
                self.add_product()
            elif choice == '7':
                self.update_stock()
            elif choice == '8':
                self.show_database_stats()
            elif choice == '9':
                print(f"\n{Fore.GREEN}{Style.BRIGHT}✨ Thank you for using Shopping Mart Admin! ✨")
                print(f"{Fore.YELLOW}Goodbye! 👋")
                break
            else:
                self.print_error("Invalid choice. Please try again.")
            
            # Pause before showing menu again
            input(f"\n{Fore.CYAN}Press Enter to continue...")

if __name__ == "__main__":
    db_name = sys.argv[1] if len(sys.argv) > 1 else 'shopping_mart.db'
    admin = DatabaseAdmin(db_name)
    admin.main_menu()