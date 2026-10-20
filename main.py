import os
import uuid
import flet as ft
from supabase import create_client

# Supabase bağlantısı
URL = "https://fayzwjfermnyjfuahgmj.supabase.co"
KEY = "sb_publishable_jLOs7DYfvEKeAzGmI_HouA_8Vx9OJXs"
BUCKET = "urun-resimleri"

sb = create_client(URL, KEY)


def main(page: ft.Page):
    page.title = "Mobil Depo Yönetimi"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15

    body = ft.Container(expand=True)
    status_text = ft.Text()

    def notify(message, error=False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
        )
        page.snack_bar.open = True
        page.update()

    def fetch(table):
        return sb.from_(table).select("*").execute().data or []

    def get_products():
        return fetch("urunler")

    def get_categories():
        return fetch("kategoriler")

    def show_error(ex):
        notify(f"İşlem başarısız: {ex}", True)

    def refresh_current():
        body.content = build_summary()
        page.update()

    # 1. ÖZET
    def build_summary():
        try:
            products = get_products()
            total_types = len(products)
            total_stock = sum(int(p.get("miktar") or 0) for p in products)
            low_stock = [
                p for p in products
                if int(p.get("miktar") or 0) <= 5
            ]

            low_controls = []
            for p in low_stock:
                low_controls.append(
                    ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.WARNING_AMBER,
                            color=ft.Colors.RED_400,
                        ),
                        title=ft.Text(p.get("name") or "İsimsiz"),
                        subtitle=ft.Text(
                            f"Stok: {p.get('miktar', 0)} adet"
                        ),
                    )
                )

            if not low_controls:
                low_controls.append(
                    ft.Text(
                        "Azalan ürün yok ✔",
                        color=ft.Colors.GREEN_400,
                    )
                )

            return ft.Column(
                [
                    ft.Text(
                        "📊 Genel Özet",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Ürün Çeşidi"),
                                        ft.Text(
                                            str(total_types),
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                bgcolor=ft.Colors.SURFACE_CONTAINER,
                                padding=15,
                                border_radius=12,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Toplam Stok"),
                                        ft.Text(
                                            str(total_stock),
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                bgcolor=ft.Colors.SURFACE_CONTAINER,
                                padding=15,
                                border_radius=12,
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Divider(),
                    ft.Text(
                        "⚠️ Azalan Stoklar (5 ve altı)",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    *low_controls,
                    ft.OutlinedButton(
                        "Yenile",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: refresh_current(),
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        except Exception as ex:
            return ft.Column(
                [
                    ft.Text("Özet yüklenemedi", size=22),
                    ft.Text(str(ex), color=ft.Colors.RED_400),
                    ft.OutlinedButton(
                        "Tekrar Dene",
                        on_click=lambda e: refresh_current(),
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            )

    # 2. ÜRÜN LİSTESİ (Fotoğraf Destekli)
    def build_products_list():
        try:
            products = get_products()
            cards = []

            for p in products:
                qty = int(p.get("miktar") or 0)
                img_url = p.get("image_url")
                
                if img_url:
                    leading_widget = ft.Image(
                        src=img_url, width=50, height=50, fit="cover", border_radius=8
                    )
                else:
                    leading_widget = ft.Icon(
                        ft.Icons.INVENTORY_2,
                        color=ft.Colors.BLUE_400,
                    )

                cards.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=leading_widget,
                            title=ft.Text(
                                p.get("name") or "İsimsiz",
                                weight=ft.FontWeight.BOLD,
                            ),
                            subtitle=ft.Text(
                                f"Barkod: {p.get('barcode') or 'Yok'}"
                            ),
                            trailing=ft.Text(
                                f"{qty} adet",
                                color=(
                                    ft.Colors.RED_400
                                    if qty <= 5
                                    else ft.Colors.GREEN_400
                                ),
                                weight=ft.FontWeight.BOLD,
                            ),
                        )
                    )
                )

            if not cards:
                cards.append(ft.Text("Henüz ürün bulunmuyor."))

            return ft.Column(
                [
                    ft.Text("📋 Ürün Listesi", size=24),
                    ft.OutlinedButton(
                        "Yenile",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: open_page(1),
                    ),
                    ft.ListView(
                        controls=cards,
                        expand=True,
                        spacing=8,
                    ),
                ],
                expand=True,
            )
        except Exception as ex:
            return ft.Column(
                [
                    ft.Text("Ürünler yüklenemedi"),
                    ft.Text(str(ex), color=ft.Colors.RED_400),
                ],
                scroll=ft.ScrollMode.AUTO,
            )

    # 3. ÜRÜN EKLE
    def build_add_product():
        name = ft.TextField(label="Ürün Adı")
        category = ft.Dropdown(label="Kategori", options=[])
        new_cat_input = ft.TextField(label="Yeni Kategori Adı", expand=True)
        barcode = ft.TextField(label="Barkod (Opsiyonel)")
        quantity = ft.TextField(
            label="Başlangıç Miktarı",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        selected_img_path = {"path": None}
        img_preview = ft.Text("Seçilen resim yok", color=ft.Colors.GREY)

        def load_cats_to_dropdown():
            try:
                cats = get_categories()
                category.options = [
                    ft.dropdown.Option(
                        key=str(c["id"]),
                        text=str(c["name"]),
                    )
                    for c in cats
                ]
                category.update()
            except Exception as ex:
                print("Kategori yükleme hatası:", ex)

        load_cats_to_dropdown()

        def add_category_click(e):
            cat_name = (new_cat_input.value or "").strip()
            if not cat_name:
                notify("Kategori adı boş olamaz.", True)
                return
            try:
                res = sb.from_("kategoriler").insert({"name": cat_name}).execute()
                if res.data:
                    new_cat_input.value = ""
                    load_cats_to_dropdown()
                    notify("Kategori eklendi.")
            except Exception as ex:
                show_error(ex)

        file_picker = ft.FilePicker(on_result=lambda e: on_file_picked(e))
        page.overlay.append(file_picker)

        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files:
                selected_img_path["path"] = e.files[0].path
                img_preview.value = f"Seçildi: {e.files[0].name}"
                img_preview.color = ft.Colors.GREEN_400
                page.update()

        save_button = ft.FilledButton(
            "Kaydet",
            icon=ft.Icons.SAVE,
        )

        def save_click(e):
            product_name = (name.value or "").strip()
            qty_text = (quantity.value or "").strip()

            if not product_name or not category.value:
                notify("Ürün adı ve kategori zorunludur.", True)
                return

            try:
                qty = int(qty_text)
                if qty < 0:
                    notify("Miktar negatif olamaz.", True)
                    return
            except ValueError:
                notify("Geçerli bir tam sayı gir.", True)
                return

            save_button.disabled = True
            page.update()

            try:
                img_url = None
                if selected_img_path["path"]:
                    ext = os.path.splitext(selected_img_path["path"])[1].lower()
                    fn = f"{uuid.uuid4().hex}{ext}"
                    with open(selected_img_path["path"], "rb") as fh:
                        mime_type = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
                        sb.storage.from_(BUCKET).upload(fn, fh.read(), {"content-type": mime_type})
                    img_url = sb.storage.from_(BUCKET).get_public_url(fn)

                result = sb.from_("urunler").insert(
                    {
                        "name": product_name,
                        "kategori_id": int(category.value),
                        "barcode": (barcode.value or "").strip() or None,
                        "miktar": qty,
                        "image_url": img_url,
                    }
                ).execute()

                if not result.data:
                    raise Exception("Ürün kaydı doğrulanamadı.")

                if qty > 0:
                    sb.from_("hareketler").insert(
                        {
                            "urun_id": result.data[0]["id"],
                            "tur": "giris",
                            "adet": qty,
                            "aciklama": "İlk Stok",
                        }
                    ).execute()

                name.value = ""
                barcode.value = ""
                quantity.value = "0"
                category.value = None
                selected_img_path["path"] = None
                img_preview.value = "Seçilen resim yok"
                img_preview.color = ft.Colors.GREY

                notify("Ürün eklendi.")
                open_page(1)

            except Exception as ex:
                show_error(ex)
            finally:
                save_button.disabled = False
                page.update()

        save_button.on_click = save_click

        return ft.Column(
            [
                ft.Text("➕ Yeni Ürün Ekle", size=24),
                name,
                category,
                ft.Row([
                    new_cat_input,
                    ft.ElevatedButton("Kategori Ekle", on_click=add_category_click)
                ]),
                barcode,
                quantity,
                ft.Row([
                    ft.ElevatedButton("Resim Seç", icon=ft.Icons.IMAGE, on_click=lambda _: file_picker.pick_files(allowed_extensions=["png", "jpg", "jpeg", "webp"])),
                    img_preview
                ]),
                save_button,
                status_text,
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # 4. STOK GİRİŞ / ÇIKIŞ
    def build_movement():
        product_dropdown = ft.Dropdown(label="Ürün Seçin")
        movement_type = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="giris", label="Giriş"),
                    ft.Radio(value="cikis", label="Çıkış"),
                ]
            ),
            value="giris",
        )
        quantity = ft.TextField(
            label="Adet",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        note = ft.TextField(label="Açıklama (Opsiyonel)")

        try:
            products = get_products()
            product_dropdown.options = [
                ft.dropdown.Option(
                    key=str(p["id"]),
                    text=str(p["name"]),
                )
                for p in products
            ]
        except Exception as ex:
            status_text.value = f"Ürünler yüklenemedi: {ex}"

        save_button = ft.FilledButton(
            "İşlemi Kaydet",
            icon=ft.Icons.CHECK,
        )

        def move_click(e):
            if not product_dropdown.value:
                notify("Önce ürün seç.", True)
                return

            try:
                qty = int((quantity.value or "").strip())
                if qty <= 0:
                    notify("Adet sıfırdan büyük olmalı.", True)
                    return
            except ValueError:
                notify("Geçerli bir adet gir.", True)
                return

            pid = int(product_dropdown.value)
            move_type = movement_type.value

            save_button.disabled = True
            page.update()

            try:
                response = (
                    sb.from_("urunler")
                    .select("miktar")
                    .eq("id", pid)
                    .execute()
                )

                if not response.data:
                    raise Exception("Ürün bulunamadı.")

                current = int(response.data[0].get("miktar") or 0)

                if move_type == "cikis" and qty > current:
                    notify(
                        f"Yetersiz stok! Mevcut stok: {current}",
                        True,
                    )
                    return

                new_qty = (
                    current + qty
                    if move_type == "giris"
                    else current - qty
                )

                updated = (
                    sb.from_("urunler")
                    .update({"miktar": new_qty})
                    .eq("id", pid)
                    .execute()
                )

                if not updated.data:
                    raise Exception(
                        "Stok güncellenemedi. Supabase izinlerini kontrol et."
                    )

                sb.from_("hareketler").insert(
                    {
                        "urun_id": pid,
                        "tur": move_type,
                        "adet": qty,
                        "aciklama": (note.value or "").strip() or None,
                    }
                ).execute()

                quantity.value = "1"
                note.value = ""

                notify("Stok işlemi kaydedildi.")
                open_page(0)

            except Exception as ex:
                show_error(ex)
            finally:
                save_button.disabled = False
                page.update()

        save_button.on_click = move_click

        return ft.Column(
            [
                ft.Text("🔄 Stok Giriş / Çıkış", size=24),
                product_dropdown,
                ft.Text("İşlem Türü"),
                movement_type,
                quantity,
                note,
                save_button,
                status_text,
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # Sayfalar
    def open_page(index):
        status_text.value = ""

        if index == 0:
            body.content = build_summary()
        elif index == 1:
            body.content = build_products_list()
        elif index == 2:
            body.content = build_add_product()
        elif index == 3:
            body.content = build_movement()

        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=lambda e: open_page(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Özet",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED,
                selected_icon=ft.Icons.INVENTORY_2,
                label="Ürünler",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADD_BOX_OUTLINED,
                selected_icon=ft.Icons.ADD_BOX,
                label="Ekle",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SWAP_VERT,
                label="Giriş/Çıkış",
            ),
        ],
    )

    body.content = build_summary()
    page.add(body)


if __name__ == "__main__":
    ft.run(main)