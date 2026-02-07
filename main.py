import flet as ft
import sqlite3
import matplotlib
import matplotlib.pyplot as plt
import base64
import csv
from io import BytesIO
from datetime import datetime

# --- ENGINEERING CONFIGURATION ---
CURRENCY = "Ft"  # Change this to "RM" or "$" as needed
matplotlib.use('Agg')

def main(page: ft.Page):
    # --- APP SETTINGS ---
    page.title = f"NPI Grocery Tracker ({CURRENCY})"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 390
    page.window_height = 844

    # --- DATABASE ---
    def init_db():
        conn = sqlite3.connect("grocery.db", check_same_thread=False)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            description TEXT,
            price REAL,
            weight REAL,
            unit TEXT,
            norm_price REAL
        )""")
        conn.commit()
        return conn

    conn = init_db()

    # --- LOGIC CENTER ---
    def normalize(price, weight, unit):
        try:
            factor = 1.0
            # Convert small units to Standard Base (kg, L)
            if unit in ["g", "ml"]: factor = 0.001
            
            base_weight = weight * factor
            return price / base_weight if base_weight > 0 else 0
        except: return 0

    def export_to_csv(e):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prices")
            rows = cursor.fetchall()
            
            filename = f"grocery_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Category", "Description", "Price Paid", "Weight", "Unit", "Normalized Price"])
                writer.writerows(rows)
            
            page.snack_bar = ft.SnackBar(ft.Text(f"📂 Saved to {filename}"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            print(ex)

    def generate_chart_image():
        cursor = conn.cursor()
        cursor.execute("SELECT description, norm_price FROM prices ORDER BY id DESC LIMIT 5")
        data = cursor.fetchall()
        
        if not data: return None

        items = [row[0] for row in data]
        prices = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(5, 3))
        bars = ax.bar(items, prices, color='#4CAF50')
        
        ax.set_ylabel(f'Price ({CURRENCY} / 1 unit)')
        ax.set_title('True Cost Comparison (Normalized)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig) 
        return img_str

    def add_record(e):
        try:
            cat = category_dropdown.value
            desc = desc_field.value
            p_val = price_field.value
            w_val = weight_field.value
            u = unit_dropdown.value
            
            if not cat:
                desc_field.error_text = "Select Category!"
                page.update()
                return

            if not p_val or not w_val:
                desc_field.error_text = "Missing Price/Weight!"
                page.update()
                return

            p = float(p_val)
            w = float(w_val)

            norm_p = normalize(p, w, u)
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prices (date, category, description, price, weight, unit, norm_price) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (date_str, cat, desc, p, w, u, norm_p))
            conn.commit()
            
            update_ui()
            desc_field.value = ""
            price_field.value = ""
            desc_field.error_text = None
            page.update()
            
        except ValueError:
            desc_field.error_text = "Check numbers!"
            page.update()

    # --- UI COMPONENTS ---
    chart_image = ft.Image(src="", width=350, height=250, fit="contain")
    history_list = ft.ListView(expand=True, spacing=10, padding=20)

    category_dropdown = ft.Dropdown(
        label="Type",
        width=100,
        options=[
            ft.dropdown.Option("Dairy"),
            ft.dropdown.Option("Meat"),
            ft.dropdown.Option("Fruit"),
            ft.dropdown.Option("Veg"),
            ft.dropdown.Option("Snack"),
            ft.dropdown.Option("Drink"),
            ft.dropdown.Option("Grain"),
            ft.dropdown.Option("House"),
        ],
    )
    desc_field = ft.TextField(label="Item / Brand", expand=True)
    price_field = ft.TextField(label=f"Price ({CURRENCY})", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    weight_field = ft.TextField(label="Weight", width=100, keyboard_type=ft.KeyboardType.NUMBER)
    unit_dropdown = ft.Dropdown(
        width=80, 
        options=[
            ft.dropdown.Option("kg"), 
            ft.dropdown.Option("g"), 
            ft.dropdown.Option("L"), 
            ft.dropdown.Option("ml"), 
            ft.dropdown.Option("pcs")
        ], 
        value="kg"
    )

    add_btn = ft.FilledButton("Save Record", on_click=add_record)
    export_btn = ft.OutlinedButton("📂 Export CSV", on_click=export_to_csv)

    def update_ui():
        cursor = conn.cursor()
        cursor.execute("SELECT category, description, price, norm_price, weight, unit FROM prices ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        
        history_list.controls.clear()
        for row in rows:
            cat, desc, price, norm, w, u = row
            base_unit = "kg" if u in ["kg", "g"] else "L" if u in ["L", "ml"] else "pcs"

            history_list.controls.append(
                ft.ListTile(
                    leading=ft.Text("🛒", size=24),
                    title=ft.Text(f"{cat}: {desc}"),
                    subtitle=ft.Text(f"Paid: {CURRENCY}{price} for {w}{u}"),
                    trailing=ft.Column([
                        ft.Text(f"{CURRENCY}{norm:.2f}", weight="bold", color="green"),
                        ft.Text(f"per {base_unit}", size=10, color="grey")
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=0)
                )
            )
        
        img_data = generate_chart_image()
        if img_data:
            chart_image.src = f"data:image/png;base64,{img_data}"
            chart_image.visible = True
        else:
            chart_image.visible = False
        page.update()

    # --- LAYOUT STRATEGY ---
    page.add(
        ft.Row([
            ft.Text("Grocery Analytics", size=20, weight="bold"),
            export_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
        chart_image,
        ft.Divider(),
        
        ft.Row([category_dropdown, desc_field]),
        
        ft.Row([price_field, weight_field, unit_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        
        # *** THE FIX IS HERE: ft.Alignment(0, 0) ***
        ft.Container(add_btn, alignment=ft.Alignment(0, 0)),
        
        ft.Divider(),
        ft.Text("Recent History:", size=16),
        history_list
    )

    update_ui()

# Use ft.app(main) to silence deprecation warning
ft.app(main)