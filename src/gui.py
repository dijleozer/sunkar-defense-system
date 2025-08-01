import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image
import cv2
import threading
import time
import math
import os
import json

from laser_control import LaserControl
from serial_comm import SerialComm
# from manuel_mode_control import ManualModeControl  # Removed for single joystick logic
# from joystick_controller import JoystickController  # No need to import here, passed from main

class SunkarGUI(ctk.CTk):
    def __init__(self, camera_manager, joystick, laser_control=None, autonomous_manager=None):
        super().__init__()
        self.title("SUNKAR Defense Interface")
        self.geometry("1280x680")
        self.resizable(False, False)
        self.camera_manager = camera_manager
        self.joystick = joystick  # Use the passed-in joystick instance
        
        # Use shared laser_control if provided, otherwise create new one
        if laser_control:
            self.laser_control = laser_control
        else:
            self.serial_comm = SerialComm(port="COM4")  # Match the port used in main.py
            self.laser_control = LaserControl(self.serial_comm)
            
        # Use provided autonomous manager or set to None
        if autonomous_manager:
            self.autonomous_manager = autonomous_manager
        else:
            self.autonomous_manager = None
            
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

        # Başlat butonu - Activates manual control mode
        self.start_button = ctk.CTkButton(self.panel, text="Başlat", width=140, height=45,
                                          fg_color="#242E3A", font=("Inter", 28), corner_radius=12, command=self.start_system)
        self.start_button.place(x=20, y=130)
        self.reset_button = ctk.CTkButton(self.panel, text="Başlangıç\nKonumuna Getir", width=140, height=45,
                                          fg_color="#242E3A", font=("Inter", 20), corner_radius=12, command=self.reset_position)
        self.reset_button.place(x=170, y=130)
        self.fire_button = ctk.CTkButton(self.panel, text="Ateş Et", width=140, height=50,
                                         fg_color="#EF4C4C", text_color="#FFFFFF",
                                         font=("Inter", 28), corner_radius=12, command=self.fire_action)
        self.fire_button.place(x=20, y=190)
        
        # Emergency Stop Button
        self.emergency_button = ctk.CTkButton(self.panel, text="ACİL DURDUR", width=140, height=50,
                                             fg_color="#FF0000", text_color="#FFFFFF",
                                             font=("Inter", 20, "bold"), corner_radius=12, command=self.emergency_stop)
        self.emergency_button.place(x=170, y=190)
        self.separator1 = ctk.CTkFrame(self.panel, height=3, width=290, fg_color="#1C222D")
        self.separator1.place(x=20, y=260)
        self.restricted_button = ctk.CTkButton(self.panel, text="Yasak Alan Kontrolleri", width=290, height=45,
                                               fg_color="#242E3A", font=("Inter", 20), text_color="#FFFFFF",
                                               corner_radius=12,  command=self.restricted_area)
        self.restricted_button.place(x=20, y=280)
        self.engage_button = ctk.CTkButton(self.panel, text="Angajman Kabul Et", width=290, height=50,
                                           fg_color="#EF4C4C", font=("Inter", 28), text_color="#FFFFFF",
                                           corner_radius=12, command=self.engage_action)
        self.engage_button.place(x=20, y=340)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.start_camera()

    def start_camera(self):
        self.camera_manager.start()
        self.update_loop()

    def start_system(self):
        """Activate manual control mode and enable joystick controls."""
        if self.start_button.cget("text") == "Aktif":
            # Deactivate system
            self.deactivate_system()
        else:
            # Activate system
            print("[GUI] 🚀 Manual control system activated!")
            self.status_box.configure(text="Manuel kontrol aktif - Joystick hazır")
            
            # Enable joystick controls
            if self.joystick and self.joystick.joystick:
                print("[GUI] ✅ Joystick controls enabled")
                # Reset joystick state
                self.joystick.position_hold_active = False
                self.joystick.last_fire_button_state = False
                self.joystick.fire_button_pressed = False
            else:
                print("[GUI] ⚠ Joystick not available")
                self.status_box.configure(text="Joystick bulunamadı!")
            
            # Change button appearance to show it's active
            self.start_button.configure(text="Aktif", fg_color="#4CAF50")

    def deactivate_system(self):
        """Deactivate manual control mode."""
        print("[GUI] ⏹ Manual control system deactivated!")
        self.status_box.configure(text="Manuel kontrol devre dışı")
        
        # Reset button appearance
        self.start_button.configure(text="Başlat", fg_color="#242E3A")

    def update_loop(self):
        frame, tracks = self.camera_manager.get_frame()
        if frame is not None:
            auto_mode = self.mode_switch.get() == 1
            selected_bbox = None
            status_message = ""
            
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
            
            # --- Autonomous Mode Control ---
            if auto_mode and self.autonomous_manager:
                # Activate autonomous mode if not already active
                if not self.auto_mode_active:
                    try:
                        self.autonomous_manager.activate()
                        self.auto_mode_active = True
                    except:
                        pass
                
                # Process autonomous mode
                try:
                    target_bbox, target_id, status = self.autonomous_manager.process_frame(frame, tracks)
                    status_message = status
                    
                    if target_bbox and target_id:
                        self.selected_track_id = target_id
                        selected_bbox = target_bbox
                        
                        # Draw target indicator
                        center = ((target_bbox[0] + target_bbox[2]) // 2, (target_bbox[1] + target_bbox[3]) // 2)
                        
                        if "firing" in status.lower():
                            # Draw red crosshair for firing
                            self.draw_crosshair(frame, center, color=(0, 0, 255), size=15, thickness=3)
                            cv2.putText(frame, "FIRING!", (center[0] - 30, center[1] - 20),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        elif "locking" in status.lower():
                            # Draw yellow crosshair for locking
                            self.draw_crosshair(frame, center, color=(0, 255, 255), size=12, thickness=2)
                            cv2.putText(frame, "LOCKING", (center[0] - 30, center[1] - 20),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        else:
                            # Draw blue crosshair for tracking
                            self.draw_crosshair(frame, center, color=(255, 0, 0), size=10, thickness=2)
                            cv2.putText(frame, "TRACKING", (center[0] - 30, center[1] - 20),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    
                    # Update status display
                    self.status_box.configure(text=f"Otonom: {status_message}")
                except:
                    self.status_box.configure(text="Otonom mod hatası")
            elif auto_mode:
                self.status_box.configure(text="Otonom mod aktif - Sistem yok")
                
            else:
                # Manual mode - joystick control
                # Joystick button for cycling selection
                button_index = 2  # Example: X button index
                button_pressed = self.joystick.get_button_pressed(button_index)
                if button_pressed and not self.last_joystick_button_state:
                    self.cycle_selected_balloon(tracks)
                self.last_joystick_button_state = button_pressed
                
                # Check fire button (red button or fire button)
                fire_button_pressed = self.joystick.get_fire_button_pressed()
                if fire_button_pressed:
                    print("[GUI] 🔥 Fire button pressed from joystick")
                    self.fire_action()
                    
                # --- Joystick motor control ---
                self.joystick.manual_mode_control()
                
                # --- Draw laser crosshair for manual mode ---
                self.draw_laser_crosshair(frame)
                
                # Deactivate autonomous mode when switching to manual
                if self.auto_mode_active:
                    self.autonomous_manager.deactivate()
                    self.auto_mode_active = False
            
            # --- Draw crosshair for selected target (manual mode) ---
            if not auto_mode and selected_bbox is not None:
                self.draw_crosshair(frame, ((selected_bbox[0] + selected_bbox[2]) // 2, (selected_bbox[1] + selected_bbox[3]) // 2))
            
            # Convert and display frame
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img)
            imgtk = CTkImage(light_image=pil_image, size=(700, 400))
            self.video_label.configure(image=imgtk)
            self.video_label.imgtk = imgtk
            
        self.after(30, self.update_loop)

    def draw_laser_crosshair(self, frame):
        """
        Draw crosshair at the actual laser firing position with calibrated offsets.
        """
        height, width = frame.shape[:2]

        # Get current camera position
        camera_pos = self.camera_manager.get_camera_position()
        servo_angle = camera_pos['servo_angle']
        stepper_angle = camera_pos['stepper_angle']

        # Calculate where the laser actually fires based on motor angles
        # This is the actual firing point, not the camera center
        
        # Convert motor angles to pixel positions
        # Servo controls vertical position (0-60 degrees maps to 0-height)
        # Stepper controls horizontal position (0-300 degrees maps to 0-width)
        
        # Calculate laser firing position
        laser_x = int((stepper_angle / 300.0) * width)  # Horizontal position
        laser_y = int((servo_angle / 60.0) * height)    # Vertical position
        
        # Load calibrated offsets
        offset_x = 0
        offset_y = 0
        try:
            if os.path.exists('manual_crosshair_offset.json'):
                with open('manual_crosshair_offset.json', 'r') as f:
                    data = json.load(f)
                    offset_x = data.get('offset_x', 0)
                    offset_y = data.get('offset_y', 0)
        except Exception as e:
            print(f"Error loading crosshair calibration: {e}")
        
        # Apply calibrated offsets
        laser_x += offset_x
        laser_y += offset_y
        
        # Ensure position is within frame bounds
        laser_x = max(0, min(width - 1, laser_x))
        laser_y = max(0, min(height - 1, laser_y))

        # Draw crosshair at actual laser firing position
        cv2.line(frame, (laser_x - 15, laser_y), (laser_x + 15, laser_y), (0, 255, 0), 2)
        cv2.line(frame, (laser_x, laser_y - 15), (laser_x, laser_y + 15), (0, 255, 0), 2)
        cv2.circle(frame, (laser_x, laser_y), 3, (0, 255, 0), -1)

        # Add label
        cv2.putText(frame, "LASER", (laser_x - 25, laser_y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Add status text in top-left corner
        cv2.putText(frame, f"Manual Mode", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Servo: {servo_angle}°", (10, height - 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Stepper: {stepper_angle}°", (10, height - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Laser: ({laser_x}, {laser_y})", (10, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def auto_fire_laser(self, duration=0.5):
        """Fire laser in auto mode."""
        self.laser_control.fire_laser(duration)

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
        """Fire the laser - called from GUI Fire button or joystick fire button."""
        if self.mode_switch.get():  # Auto mode
            # In auto mode, fire at the lowest ID balloon
            frame, tracks = self.camera_manager.get_frame()
            if tracks:
                # Find balloon with lowest ID
                lowest_id_track = min(tracks, key=lambda x: x['track_id'])
                print(f"[GUI] 🔥 Auto mode firing at balloon ID: {lowest_id_track['track_id']}")
                self.laser_control.fire_laser()
                self.status_box.configure(text=f"Auto Ateş: ID {lowest_id_track['track_id']}")
            else:
                self.status_box.configure(text="Hedef bulunamadı")
        else:  # Manual mode
            # In manual mode, fire directly
            print("[GUI] 🔥 Manual mode firing")
            self.laser_control.fire_laser()
            self.status_box.configure(text="Manuel Ateş Edildi!")
            
    def emergency_stop(self):
        """Emergency stop - immediately stop all operations."""
        print("[GUI] 🚨 EMERGENCY STOP ACTIVATED!")
        self.status_box.configure(text="ACİL DURDUR AKTİF!")
        
        # Stop autonomous mode
        if hasattr(self, 'autonomous_manager'):
            self.autonomous_manager.emergency_stop()
            
        # Stop laser
        if self.laser_control:
            self.laser_control.emergency_stop()
            
        # Switch to manual mode
        self.mode_switch.select(0)  # Manual mode
        
        # Deactivate system
        self.deactivate_system()
        
        print("[GUI] ✅ All systems stopped safely")

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
