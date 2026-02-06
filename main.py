import flet as ft

def main(page: ft.Page):
    # --- APP CONFIGURATION ---
    page.title = "NPI Grocery Tracker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 390  # Simulate Mobile Width
    page.window_height = 844
    
    # --- DATA & LOGIC ---
    grocery_list = []

    def add_item(e):
        try:
            # 1. Get inputs
            p = float(price_field.value)
            w = float(weight_field.value)
            
            # 2. Logic: Normalize Price
            # Avoid division by zero
            norm_p = p / w if w > 0 else 0
            
            # 3. Add to local list
            grocery_list.append(f"{desc_field.value}: ${norm_p:.2f}/unit")
            
            # 4. Update UI (Visual Feedback)
            list_view.controls.append(
                ft.Text(f"{desc_field.value} (${p}) -> Norm: ${norm_p:.2f}")
            )
            
            # 5. Clear inputs for next entry
            price_field.value = ""
            desc_field.value = ""
            page.update()
            
        except ValueError:
            price_field.error_text = "Numbers only!"
            page.update()

    # --- UI ELEMENTS ---
    desc_field = ft.TextField(label="Description (e.g., Cheddar)", width=300)
    price_field = ft.TextField(label="Price ($)", width=140, keyboard_type=ft.KeyboardType.NUMBER)
    weight_field = ft.TextField(label="Weight (kg/L)", width=140, keyboard_type=ft.KeyboardType.NUMBER)
    
    add_btn = ft.ElevatedButton("Add Record", on_click=add_item)
    
    list_view = ft.Column(scroll=ft.ScrollMode.AUTO, height=400)

    # --- LAYOUT STRATEGY ---
    page.add(
        ft.Row([ft.Text("Grocery Analyst", size=24, weight="bold")], alignment="center"),
        ft.Divider(),
        ft.Row([desc_field], alignment="center"),
        ft.Row([price_field, weight_field], alignment="center"),
        ft.Row([add_btn], alignment="center"),
        ft.Divider(),
        ft.Text("History:", size=16),
        list_view
    )

ft.app(target=main)