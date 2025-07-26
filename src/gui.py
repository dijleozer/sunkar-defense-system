import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image
import cv2
import threading
import time
import math

from manuel_mode_control import ManualModeControl
from laser_control import LaserControl
from serial_comm import SerialComm
from joystick_controller import JoystickController

class SunkarGUI(ctk.CTk):
    def __init__(self, camera_manager):
        super().__init__()
        self.title("SUNKAR Defense Interface")
        self.geometry("1280x680")
        self.resizable(False, False)
        self.camera_manager = camera_manager
        self.manual_control = None
        self.serial_comm = SerialComm(port="COM3")  # Arduino’nun bağlı olduğu doğru portu yaz
        self.laser_control = LaserControl(self.serial_comm)
        self.joystick = JoystickController(port="COM3", mode="manual")
        self.selected_track_id = None
        self.last_joystick_button_state = False
        self.bind("<Button-1>", self.on_video_click)  # Mouse click event
        self.auto_fired_ids = set()  # Track which balloons have been fired at in auto mode
        self.auto_mode_active = False
        self.crosshair_timer = 0  # Number of frames to keep crosshair visible
        self.crosshair_bbox = None  # The bbox to keep crosshair on
        self.crosshair_track_id = None  # Track ID to keep crosshair on in auto mode
        self.restricted_container = None  # Will be created on demand

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color="#1C222D")

        # Ana container (pencerenin ortasında olacak)
        self.main_container = ctk.CTkFrame(self, width=1140, height=600, fg_color="#131820", corner_radius=24)
        self.main_container.place(relx=0.5, rely=0.5, anchor="center")

        # 3 sütunlu grid
        self.main_container.grid_columnconfigure((0, 1, 2), weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Sol taraf: Kamera + alt kısımlar için Frame (2 sütun kaplayacak)
        self.camera_frame = ctk.CTkFrame(self.main_container, fg_color="#131820", corner_radius=24)
        self.camera_frame.grid(row=0, column=0, columnspan=2, padx=(20, 10), pady=20, sticky="nsew")

        # Kamera görüntüsü
        self.video_label = ctk.CTkLabel(self.camera_frame, text="", width=700, height=400, corner_radius=12)
        self.video_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10))

        # Sistem durumu
        self.status_box = ctk.CTkLabel(self.camera_frame, text="Sistem Başlatıldı.", width=340, height=80,
                                       fg_color="#242E3A", corner_radius=12, font=("Inter", 20),
                                       anchor="center", justify="center")
        self.status_box.grid(row=1, column=0, padx=(20, 10), pady=(50, 30), sticky="nsew")

        # Zoom butonları çerçevesi
        self.zoom_frame = ctk.CTkFrame(self.camera_frame, width=340, height=80, fg_color="#242E3A", corner_radius=12)
        self.zoom_frame.grid(row=1, column=1, padx=(10, 20), pady=(50, 30), sticky="nsew")

        # Zoom butonlarını grid ile ortala
        self.zoom_frame.grid_columnconfigure((0, 1), weight=1)
        self.zoom_frame.grid_rowconfigure(0, weight=1)
        
        self.zoom_in = ctk.CTkButton(self.zoom_frame, text="Yaklaştır", font=("Inter", 20), height=50)
        self.zoom_in.grid(row=0, column=0, padx=10, pady=15, sticky="ew")

        self.zoom_out = ctk.CTkButton(self.zoom_frame, text="Uzaklaştır", font=("Inter", 20), height=50)
        self.zoom_out.grid(row=0, column=1, padx=10, pady=15, sticky="ew")

        # Sağ taraf: Kontrol paneli için Frame (1 sütun)
        self.panel = ctk.CTkFrame(self.main_container, width=320, height=540, fg_color="#131820", corner_radius=24)
        self.panel.grid(row=0, column=2, padx=(5, 20), pady=20, sticky="n")

        # Kontrol Modu başlığı
        self.control_label = ctk.CTkLabel(self.panel, text="Kontrol Modu", font=("Inter", 28, "bold"), text_color="#FFFFFF")
        self.control_label.place(x=20, y=20)

        # Manuel / Auto switch ve label'ları
        self.manual_label = ctk.CTkLabel(self.panel, text="Manuel", font=("Inter", 28), text_color="#8892A6")
        self.manual_label.place(x=20, y=70)

        self.mode_switch = ctk.CTkSwitch(self.panel, text="", width=70)
        self.mode_switch.place(x=130, y=75)

        self.auto_label = ctk.CTkLabel(self.panel, text="Auto", font=("Inter", 28), text_color="#8892A6")
        self.auto_label.place(x=200, y=70)

        # Başlat butonu
        self.start_button = ctk.CTkButton(self.panel, text="Başlat", width=140, height=45,
                                          fg_color="#242E3A", font=("Inter", 28), corner_radius=12, command=self.start_system)
        self.start_button.place(x=20, y=130)

        # Başlangıç Konumuna Getir butonu (iki satır yazı, aynı genişlikte olacak)
        self.reset_button = ctk.CTkButton(self.panel, text="Başlangıç\nKonumuna Getir", width=140, height=45,
                                          fg_color="#242E3A", font=("Inter", 20), corner_radius=12, command=self.reset_position)
        self.reset_button.place(x=170, y=130)

        # Ateş Et butonu
        self.fire_button = ctk.CTkButton(self.panel, text="Ateş Et", width=290, height=50,
                                         fg_color="#EF4C4C", text_color="#FFFFFF",
                                         font=("Inter", 28, "bold"), corner_radius=12, command=self.fire_action)
        self.fire_button.place(x=20, y=200)

        # Ayırıcı çizgi
        self.separator1 = ctk.CTkFrame(self.panel, height=3, width=290, fg_color="#1C222D")
        self.separator1.place(x=20, y=260)

        # Yasak Alan Kontrolleri butonu
        self.restricted_button = ctk.CTkButton(self.panel, text="Yasak Alan Kontrolleri", width=290, height=45,
                                               fg_color="#242E3A", font=("Inter", 20), text_color="#FFFFFF",
                                               corner_radius=12,  command=self.restricted_area)
        self.restricted_button.place(x=20, y=280)

        # Angajman Kabul Et butonu
        self.engage_button = ctk.CTkButton(self.panel, text="Angajman Kabul Et", width=290, height=50,
                                           fg_color="#EF4C4C", font=("Inter", 28), text_color="#FFFFFF",
                                           corner_radius=12, command=self.engage_action)
        self.engage_button.place(x=20, y=340)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.start_camera()

    def start_camera(self):
        self.camera_manager.start()
        self.update_loop()

    def update_loop(self):
        frame, tracks = self.camera_manager.get_frame()
        if frame is not None:
            auto_mode = self.mode_switch.get() == 1
            selected_bbox = None

            # --- Always draw bounding boxes for all detections ---
            for det in tracks:
                x1, y1, x2, y2 = det['bbox']
                track_id = det['track_id']
                color = (0, 255, 0)
                # Highlight the selected target in red
                if track_id == self.selected_track_id:
                    color = (0, 0, 255)
                    selected_bbox = (x1, y1, x2, y2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"ID:{track_id} {det['label']}", (x1, max(0, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # --- Autonomous targeting logic with debug prints ---
            if auto_mode:
                red_balloons = [det for det in tracks if det['label'].lower() == "red"]
                print(f"[AUTO] Detected red balloons: {[{'id': b['track_id'], 'bbox': b['bbox']} for b in red_balloons]}")
                if red_balloons:
                    candidates = [b for b in red_balloons if b['track_id'] not in self.auto_fired_ids]
                    if candidates:
                        target = min(candidates, key=lambda d: d['track_id'])
                        self.selected_track_id = target['track_id']
                        selected_bbox = target['bbox']
                        print(f"[AUTO] Targeting balloon: track_id={target['track_id']}, bbox={target['bbox']}")
                        # Fire laser only once per target
                        if target['track_id'] not in self.auto_fired_ids:
                            self.auto_fired_ids.add(target['track_id'])
                            threading.Thread(target=self.auto_fire_laser, args=(0.5,), daemon=True).start()
                            # Keep crosshair on this track_id
                            self.crosshair_track_id = target['track_id']
                        self.status_box.configure(text=f"Otonom: Hedeflenen balon ID {target['track_id']}")
                    else:
                        print("[AUTO] All red balloons have been targeted already.")
                        self.status_box.configure(text="Otonom: Kırmızı balon kalmadı.")
                        self.selected_track_id = None
                else:
                    print("[AUTO] No red balloons detected in this frame.")
                    self.status_box.configure(text="Otonom: Kırmızı balon yok.")
                    self.selected_track_id = None
            else:
                # Joystick button for cycling selection
                button_index = 2  # Example: X button index
                button_pressed = self.joystick.get_button_pressed(button_index)
                if button_pressed and not self.last_joystick_button_state:
                    self.cycle_selected_balloon(tracks)
                self.last_joystick_button_state = button_pressed

                # Check B button (index 1) for firing
                b_button_index = 1
                b_button_pressed = self.joystick.get_button_pressed(b_button_index)
                if b_button_pressed and not getattr(self, 'last_b_button_state', False):
                    self.fire_action()
                self.last_b_button_state = b_button_pressed

            # --- Draw crosshair for selected target (auto or manual) ---
            crosshair_drawn = False
            if selected_bbox is not None:
                self.draw_crosshair(frame, ((selected_bbox[0] + selected_bbox[2]) // 2, (selected_bbox[1] + selected_bbox[3]) // 2))
                crosshair_drawn = True
            # In auto mode, keep crosshair on last targeted object as long as it is present
            if auto_mode and not crosshair_drawn and self.crosshair_track_id is not None:
                # Find the bbox for the last targeted track_id
                for det in tracks:
                    if det['track_id'] == self.crosshair_track_id:
                        bbox = det['bbox']
                        cx = (bbox[0] + bbox[2]) // 2
                        cy = (bbox[1] + bbox[3]) // 2
                        self.draw_crosshair(frame, (cx, cy))
                        crosshair_drawn = True
                        break
                # If the object is no longer present, remove the crosshair
                if not crosshair_drawn:
                    self.crosshair_track_id = None

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img)
            imgtk = CTkImage(light_image=pil_image, size=(700, 400))
            self.video_label.configure(image=imgtk)
            self.video_label.imgtk = imgtk
        self.after(30, self.update_loop)

    def auto_fire_laser(self, duration=0.5):
        # Autonomous mode: do NOT check no-fire zone, always fire if logic allows
        self.laser_control.turn_on()
        time.sleep(duration)
        self.laser_control.turn_off()

    def start_joystick_loop(self):
        def joystick_loop():
            while self.manual_control.is_manual_mode:
                self.manual_control.joystick_input()
                time.sleep(0.1)  # 10 Hz joystick polling rate
        threading.Thread(target=joystick_loop, daemon=True).start()

    def start_system(self):
        mode = self.mode_switch.get()
        if mode == 0:
            self.status_box.configure(text="Manuel Mod Başlatıldı.")
            print("Manuel mod başlatılıyor...")
            self.auto_fired_ids.clear()
            self.auto_mode_active = False
            # ManualModeControl başlat
            self.manual_control = ManualModeControl(self.camera_manager, self.laser_control, self.joystick)
            self.manual_control.switch_to_manual()
            self.start_joystick_loop()
        else:
            self.status_box.configure(text="Otonom Mod Başlatıldı.")
            print("Otonom mod başlatılıyor...")
            self.auto_fired_ids.clear()
            self.auto_mode_active = True

    def reset_position(self):
        self.camera_manager.reset_position()
        self.status_box.configure(text="Başlangıç konumuna getirildi.")
        print("Reset butonu çalıştı.")

    def draw_crosshair(self, frame, center, color=(0,0,255), size=10, thickness=2):
        x, y = center
        cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
        cv2.line(frame, (x, y - size), (x, y + size), color, thickness)
        cv2.circle(frame, (x, y), 3, color, -1)

    def on_video_click(self, event):
        frame, tracks = self.camera_manager.get_frame()
        if frame is None:
            return

        display_w, display_h = self.video_label.winfo_width(), self.video_label.winfo_height()
        frame_h, frame_w = frame.shape[:2]

        x_img = int(event.x * frame_w / display_w)
        y_img = int(event.y * frame_h / display_h)

        for det in tracks:
            x1, y1, x2, y2 = det['bbox']
            if x1 <= x_img <= x2 and y1 <= y_img <= y2:
                self.selected_track_id = det['track_id']
                break

    def cycle_selected_balloon(self, tracks):
        track_ids = [det['track_id'] for det in tracks]
        if not track_ids:
            self.selected_track_id = None
            return
        if self.selected_track_id not in track_ids:
            self.selected_track_id = track_ids[0]
        else:
            idx = track_ids.index(self.selected_track_id)
            self.selected_track_id = track_ids[(idx + 1) % len(track_ids)]

    def fire_action(self):
        frame, tracks = self.camera_manager.get_frame()
        selected_bbox = None
        for det in tracks:
            if det['track_id'] == self.selected_track_id:
                selected_bbox = det['bbox']
                break
        # Get current stepper angle from manual_control
        h_angle, _ = self.manual_control.get_last_angles() if hasattr(self.manual_control, 'get_last_angles') else (0, 0)
        # Get no-fire zone angles
        start_angle_str = self.fire_start_entry.get()
        end_angle_str = self.fire_end_entry.get()
        try:
            start_angle = float(start_angle_str)
            end_angle = float(end_angle_str)
            angles_valid = True
        except Exception:
            angles_valid = False
        # Only restrict if both angles are valid and not empty
        if angles_valid and start_angle_str.strip() != '' and end_angle_str.strip() != '':
            if self.is_angle_in_sector(h_angle, start_angle, end_angle):
                self.status_box.configure(text="Restricted Area")
                return
        if selected_bbox and self.manual_control.is_balloon_centered(selected_bbox, frame.shape):
            self.manual_control.fire_laser()
            self.status_box.configure(text="ATEŞ EDİLDİ!")
        else:
            self.status_box.configure(text="Ateş edilemez, hedef ortalanmadı.")

    def is_angle_in_sector(self, angle, start, end):
        # Normalize angles to [0, 360)
        angle = angle % 360
        start = start % 360
        end = end % 360
        if start < end:
            return start <= angle <= end
        else:
            return angle >= start or angle <= end

    def show_main_page(self):
        self.main_container.place(relx=0.5, rely=0.5, anchor="center")
        if self.restricted_container:
            self.restricted_container.place_forget()

    def show_restricted_page(self):
        self.main_container.place_forget()
        if not self.restricted_container:
            self.create_restricted_container()
        self.restricted_container.place(relx=0.5, rely=0.5, anchor="center")

    def restricted_area(self):
        self.status_box.configure(text="Yasak Alan Kontrolleri aktif.")
        print("Yasak Alan Kontrolleri butonu çalıştı.")
        self.show_restricted_page()

    def create_restricted_container(self):
        self.restricted_container = ctk.CTkFrame(self, width=1140, height=600, fg_color="#131820", corner_radius=24)
        self.restricted_container.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = ctk.CTkLabel(self.restricted_container, text="Yasak Alan Kontrolü", font=("Inter", 36, "bold"), text_color="#FFFFFF")
        title.place(relx=0.5, rely=0.08, anchor="n")

        # Main content frame for both zones (side by side, like main page)
        content_frame = ctk.CTkFrame(self.restricted_container, width=1040, height=480, fg_color="#232C39", corner_radius=18)
        content_frame.place(relx=0.5, rely=0.18, anchor="n")
        content_frame.grid_columnconfigure((0, 1), weight=1, uniform="zone")
        content_frame.grid_rowconfigure(0, weight=1)

        # --- No-Fire Zone (left) ---
        fire_zone_frame = ctk.CTkFrame(content_frame, width=500, height=440, fg_color="#232C39", corner_radius=18)
        fire_zone_frame.grid(row=0, column=0, padx=(30, 15), pady=20, sticky="nsew")
        fire_zone_frame.grid_columnconfigure(0, weight=1)

        fire_zone_label = ctk.CTkLabel(fire_zone_frame, text="Atışa Yasak Alan", font=("Inter", 26, "bold"), text_color="#FFFFFF")
        fire_zone_label.grid(row=0, column=0, pady=(10, 10), sticky="n")

        # Add hareket_resmi.jpg image (same as No-Movement Zone)
        self.fire_hareket_img_orig = Image.open("hareket_resmi.jpg").resize((420, 240))
        self.fire_hareket_img = self.fire_hareket_img_orig.copy()
        self.fire_hareket_imgtk = CTkImage(light_image=self.fire_hareket_img, size=(420, 240))
        self.fire_hareket_label = ctk.CTkLabel(fire_zone_frame, image=self.fire_hareket_imgtk, text="", width=420, height=240)
        self.fire_hareket_label.grid(row=1, column=0, pady=(0, 20), sticky="n")

        # Angle input fields and button (copied from No-Movement Zone)
        self.fire_start_entry = ctk.CTkEntry(fire_zone_frame, placeholder_text="Başlangıç Açısı", width=200)
        self.fire_start_entry.grid(row=2, column=0, pady=(0, 10), sticky="n")
        self.fire_end_entry = ctk.CTkEntry(fire_zone_frame, placeholder_text="Bitiş Açısı", width=200)
        self.fire_end_entry.grid(row=3, column=0, pady=(0, 10), sticky="n")
        fire_save_btn = ctk.CTkButton(fire_zone_frame, text="Kaydet", width=120, command=self.save_fire_zone)
        fire_save_btn.grid(row=4, column=0, pady=(0, 10), sticky="n")

        # --- No-Movement Zone (right) ---
        move_zone_frame = ctk.CTkFrame(content_frame, width=500, height=440, fg_color="#232C39", corner_radius=18)
        move_zone_frame.grid(row=0, column=1, padx=(15, 30), pady=20, sticky="nsew")
        move_zone_frame.grid_columnconfigure(0, weight=1)

        move_zone_label = ctk.CTkLabel(move_zone_frame, text="Harekete Yasak Alan", font=("Inter", 26, "bold"), text_color="#FFFFFF")
        move_zone_label.grid(row=0, column=0, pady=(10, 10), sticky="n")

        # Smaller image size (e.g., 420x240)
        hareket_img = Image.open("hareket_resmi.jpg").resize((420, 240))
        hareket_imgtk = CTkImage(light_image=hareket_img, size=(420, 240))
        hareket_label = ctk.CTkLabel(move_zone_frame, image=hareket_imgtk, text="", width=420, height=240)
        hareket_label.grid(row=1, column=0, pady=(0, 20), sticky="n")

        move_start_entry = ctk.CTkEntry(move_zone_frame, placeholder_text="Başlangıç Açısı", width=200)
        move_start_entry.grid(row=2, column=0, pady=(0, 10), sticky="n")
        move_end_entry = ctk.CTkEntry(move_zone_frame, placeholder_text="Bitiş Açısı", width=200)
        move_end_entry.grid(row=3, column=0, pady=(0, 10), sticky="n")
        move_save_btn = ctk.CTkButton(move_zone_frame, text="Kaydet", width=120)
        move_save_btn.grid(row=4, column=0, pady=(0, 10), sticky="n")

        # Return button
        return_btn = ctk.CTkButton(self.restricted_container, text="Geri Dön", width=200, height=45, font=("Inter", 22), command=self.show_main_page)
        return_btn.place(relx=0.5, rely=0.93, anchor="center")

        self.update_restricted_video()

    def update_restricted_video(self):
        if self.restricted_container and self.restricted_container.winfo_ismapped():
            frame, _ = self.camera_manager.get_frame()
            if frame is not None:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(img)
                imgtk = CTkImage(light_image=pil_image, size=(700, 400))
                self.restricted_video_label.configure(image=imgtk)
                self.restricted_video_label.imgtk = imgtk
            self.after(30, self.update_restricted_video)

    def save_fire_zone(self):
        try:
            start_angle = float(self.fire_start_entry.get())
            end_angle = float(self.fire_end_entry.get())
        except ValueError:
            return  # Invalid input, do nothing
        # Draw sector (pie slice) with 0° at x-axis (right, 3 o'clock), counterclockwise
        img = self.fire_hareket_img_orig.copy()
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img, 'RGBA')
        cx, cy = img.width // 2, img.height // 2
        r = min(cx, cy) - 10
        # PIL pieslice: 0° is at 3 o'clock, counterclockwise, which matches the coordinate system
        # So, use angles directly
        draw.pieslice([cx - r, cy - r, cx + r, cy + r], start_angle, end_angle, fill=(255, 0, 0, 120))
        self.fire_hareket_img = img
        self.fire_hareket_imgtk = CTkImage(light_image=img, size=(420, 240))
        self.fire_hareket_label.configure(image=self.fire_hareket_imgtk)
        self.fire_hareket_label.imgtk = self.fire_hareket_imgtk

    def engage_action(self):
        self.status_box.configure(text="Angajman kabul edildi.")
        print("Angajman Kabul Et butonu çalıştı.")

    def on_close(self):
        self.camera_manager.stop()
        self.destroy() 