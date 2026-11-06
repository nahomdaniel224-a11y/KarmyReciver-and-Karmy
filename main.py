
import socket
import struct
import threading
import queue
import tkinter as tk
from fractions import Fraction
from tkinter import messagebox

import av
import customtkinter as ctk
from PIL import Image, ImageTk


# ============================================================
# KARMY RECEIVER - PC KARMA
# ============================================================

APP_NAME = "KarmyReceiver"
PORT = 47831
PROTOCOL = b"KARMY-H264-2"

BG = "#080D12"
PANEL = "#111B25"
PANEL_LIGHT = "#192633"
GREEN = "#34A853"
GREEN_DARK = "#237A3A"
WHITE = "#F5F7FA"
MUTED = "#91A0AE"
RED = "#F15B5B"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class KarmyReceiver:

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title(APP_NAME)
        self.root.configure(fg_color=BG)

        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda event: None)

        self.running = True
        self.connected = False
        self.video_started = False

        self.sock = None
        self.receiver_thread = None

        self.events = queue.Queue()
        self.frames = queue.Queue(maxsize=1)

        self.current_photo = None
        self.animation_position = 0
        self.animation_direction = 1

        self.video_canvas = None
        self.waiting_screen = None
        self.connection_screen = None

        self.build_interface()

        self.root.after(30, self.process_events)
        self.root.after(30, self.animate_waiting)

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    # --------------------------------------------------------
    # INTERFACE
    # --------------------------------------------------------

    def build_interface(self):

        self.main = ctk.CTkFrame(
            self.root,
            fg_color=BG,
            corner_radius=0
        )
        self.main.pack(fill="both", expand=True)

        # Top bar
        self.topbar = ctk.CTkFrame(
            self.main,
            fg_color=BG,
            corner_radius=0,
            height=75
        )
        self.topbar.pack(fill="x", padx=35, pady=(18, 0))
        self.topbar.pack_propagate(False)

        ctk.CTkLabel(
            self.topbar,
            text="KARMY",
            font=("Segoe UI", 25, "bold"),
            text_color=WHITE
        ).pack(side="left", pady=12)

        ctk.CTkLabel(
            self.topbar,
            text="PC KARMA  •  WINDOWS RECEIVER",
            font=("Segoe UI", 11, "bold"),
            text_color=MUTED
        ).pack(side="left", padx=16, pady=18)

        self.make_exit_button()

        # Main content
        self.content = ctk.CTkFrame(
            self.main,
            fg_color=BG,
            corner_radius=0
        )
        self.content.pack(fill="both", expand=True)

        self.build_waiting_screen()

        # Bottom-right minimize control
        self.make_minimize_button()

    def make_exit_button(self):

        self.exit_area = ctk.CTkFrame(
            self.topbar,
            fg_color=PANEL,
            corner_radius=12,
            width=65,
            height=48
        )
        self.exit_area.pack(side="right", pady=10)
        self.exit_area.pack_propagate(False)

        icon = tk.Canvas(
            self.exit_area,
            width=65,
            height=48,
            bg=PANEL,
            highlightthickness=0,
            cursor="hand2"
        )
        icon.pack(fill="both", expand=True)

        # Door
        icon.create_line(
            15, 10, 15, 38,
            fill=WHITE, width=2
        )
        icon.create_line(
            15, 10, 34, 10,
            fill=WHITE, width=2
        )
        icon.create_line(
            34, 10, 34, 38,
            fill=WHITE, width=2
        )
        icon.create_line(
            15, 38, 34, 38,
            fill=WHITE, width=2
        )

        # Arrow pointing right
        icon.create_line(
            25, 24, 51, 24,
            fill=GREEN, width=3,
            arrow=tk.LAST,
            arrowshape=(8, 9, 4)
        )

        icon.bind("<Button-1>", lambda event: self.exit_app())

    def make_minimize_button(self):

        self.minimize_area = ctk.CTkFrame(
            self.main,
            fg_color=PANEL,
            corner_radius=12,
            width=48,
            height=42
        )

        self.minimize_area.place(
            relx=0.98,
            rely=0.97,
            anchor="se"
        )

        icon = tk.Canvas(
            self.minimize_area,
            width=48,
            height=42,
            bg=PANEL,
            highlightthickness=0,
            cursor="hand2"
        )
        icon.pack(fill="both", expand=True)

        icon.create_line(
            13, 21, 35, 21,
            fill=WHITE,
            width=3,
            capstyle=tk.ROUND
        )

        icon.bind("<Button-1>", lambda event: self.minimize_app())

    # --------------------------------------------------------
    # WAITING SCREEN
    # --------------------------------------------------------

    def build_waiting_screen(self):

        self.waiting_screen = ctk.CTkFrame(
            self.content,
            fg_color=BG,
            corner_radius=0
        )
        self.waiting_screen.pack(
            fill="both",
            expand=True
        )

        card = ctk.CTkFrame(
            self.waiting_screen,
            fg_color=PANEL,
            corner_radius=25,
            width=530,
            height=470
        )
        card.place(
            relx=0.5,
            rely=0.48,
            anchor="center"
        )
        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text="Connect your phone",
            font=("Segoe UI", 27, "bold"),
            text_color=WHITE
        ).pack(pady=(35, 7))

        ctk.CTkLabel(
            card,
            text="Open Karmy on your Android phone and start casting.",
            font=("Segoe UI", 12),
            text_color=MUTED
        ).pack(pady=(0, 20))

        self.animation_canvas = tk.Canvas(
            card,
            width=270,
            height=75,
            bg=PANEL,
            highlightthickness=0
        )
        self.animation_canvas.pack()

        self.status_label = ctk.CTkLabel(
            card,
            text="Waiting for connection...",
            font=("Segoe UI", 15, "bold"),
            text_color=GREEN
        )
        self.status_label.pack(pady=(5, 20))

        self.ip_entry = ctk.CTkEntry(
            card,
            width=320,
            height=45,
            placeholder_text="Enter your phone's IP address",
            font=("Segoe UI", 14),
            corner_radius=10,
            fg_color=PANEL_LIGHT,
            border_color="#344555"
        )
        self.ip_entry.pack(pady=5)

        self.connect_button = ctk.CTkButton(
            card,
            text="Connect",
            width=320,
            height=45,
            font=("Segoe UI", 14, "bold"),
            fg_color=GREEN_DARK,
            hover_color=GREEN,
            corner_radius=10,
            command=self.connect_phone
        )
        self.connect_button.pack(pady=(12, 12))

        ctk.CTkLabel(
            card,
            text=f"Same Wi-Fi network  •  TCP Port {PORT}",
            font=("Segoe UI", 11),
            text_color=MUTED
        ).pack(pady=5)

    # --------------------------------------------------------
    # CONNECTION ANIMATION
    # --------------------------------------------------------

    def animate_waiting(self):

        if not self.running:
            return

        if not self.connected and self.animation_canvas:

            canvas = self.animation_canvas
            canvas.delete("all")

            canvas.create_line(
                30, 37, 240, 37,
                fill="#344555",
                width=3
            )

            # Moving circle
            x = 30 + self.animation_position

            canvas.create_oval(
                x - 9, 28,
                x + 9, 46,
                fill=GREEN,
                outline=GREEN
            )

            self.animation_position += (
                5 * self.animation_direction
            )

            if self.animation_position >= 190:
                self.animation_direction = -1

            elif self.animation_position <= 0:
                self.animation_direction = 1

        self.root.after(30, self.animate_waiting)

    # --------------------------------------------------------
    # TCP CONNECTION
    # --------------------------------------------------------

    @staticmethod
    def receive_exact(sock, size):

        data = bytearray()

        while len(data) < size:
            part = sock.recv(size - len(data))

            if not part:
                raise ConnectionError("Phone disconnected.")

            data.extend(part)

        return bytes(data)

    def connect_phone(self):

        if self.connected:
            return

        ip = self.ip_entry.get().strip()

        if not ip:
            messagebox.showwarning(
                "Karmy",
                "Enter your phone's IP address first."
            )
            return

        self.connect_button.configure(
            text="Connecting...",
            state="disabled"
        )

        self.status_label.configure(
            text="Connecting to phone...",
            text_color=GREEN
        )

        self.receiver_thread = threading.Thread(
            target=self.connection_worker,
            args=(ip,),
            daemon=True
        )
        self.receiver_thread.start()

    def connection_worker(self, ip):

        try:
            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            sock.settimeout(15)
            sock.connect((ip, PORT))
            sock.settimeout(None)
            sock.setsockopt(
                socket.IPPROTO_TCP,
                socket.TCP_NODELAY,
                1
            )

            self.sock = sock

            # Read protocol identifier
            magic = self.receive_exact(
                sock,
                len(PROTOCOL)
            )

            if magic != PROTOCOL:
                raise ValueError(
                    "Unsupported Karmy stream protocol."
                )

            # Read width and height
            width, height = struct.unpack(
                ">ii",
                self.receive_exact(sock, 8)
            )

            if not (1 <= width <= 8192 and 1 <= height <= 8192):
                raise ValueError("Invalid video dimensions.")

            # Read codec configuration
            csd0_size = struct.unpack(
                ">i",
                self.receive_exact(sock, 4)
            )[0]

            if not 0 < csd0_size <= 1024 * 1024:
                raise ValueError("Invalid H.264 configuration.")

            csd0 = self.receive_exact(sock, csd0_size)

            csd1_size = struct.unpack(
                ">i",
                self.receive_exact(sock, 4)
            )[0]

            if not 0 < csd1_size <= 1024 * 1024:
                raise ValueError("Invalid H.264 configuration.")

            csd1 = self.receive_exact(sock, csd1_size)

            # Prepare H.264 decoder
            decoder = av.CodecContext.create(
                "h264",
                "r"
            )

            decoder.extradata = csd0 + csd1
            decoder.open()

            self.events.put(
                ("connected", (width, height))
            )

            # Receive video packets
            while self.running:

                packet_size = struct.unpack(
                    ">i",
                    self.receive_exact(sock, 4)
                )[0]

                if not 0 < packet_size <= 16 * 1024 * 1024:
                    raise ValueError("Invalid video packet size.")

                timestamp = struct.unpack(
                    ">q",
                    self.receive_exact(sock, 8)
                )[0]

                flags = struct.unpack(
                    ">i",
                    self.receive_exact(sock, 4)
                )[0]

                payload = self.receive_exact(
                    sock,
                    packet_size
                )

                packet = av.Packet(payload)
                packet.pts = timestamp
                packet.dts = timestamp
                packet.time_base = Fraction(1, 1_000_000)

                decoded_frames = decoder.decode(packet)

                for frame in decoded_frames:

                    image = frame.to_image().convert("RGB")

                    if self.frames.full():
                        try:
                            self.frames.get_nowait()
                        except queue.Empty:
                            pass

                    try:
                        self.frames.put_nowait(image)
                    except queue.Full:
                        pass

        except Exception as error:

            if self.running:
                self.events.put(
                    ("error", str(error))
                )

        finally:

            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass

                self.sock = None

    # --------------------------------------------------------
    # SUCCESS ANIMATION AND DISPLAY
    # --------------------------------------------------------

    def show_success(self, dimensions):

        self.connected = True

        self.waiting_screen.pack_forget()

        self.connection_screen = ctk.CTkFrame(
            self.content,
            fg_color=BG,
            corner_radius=0
        )
        self.connection_screen.pack(
            fill="both",
            expand=True
        )

        center = ctk.CTkFrame(
            self.connection_screen,
            fg_color=BG,
            corner_radius=0
        )
        center.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.success_label = ctk.CTkLabel(
            center,
            text="✓",
            font=("Segoe UI", 75, "bold"),
            text_color=GREEN
        )
        self.success_label.pack()

        self.success_status = ctk.CTkLabel(
            center,
            text="Connected!",
            font=("Segoe UI", 23, "bold"),
            text_color=WHITE
        )
        self.success_status.pack(pady=10)

        # Tick visible for 0.1 seconds,
        # then wait 1.2 seconds before showing video.
        self.root.after(
            100,
            self.start_display_delay
        )

    def start_display_delay(self):

        if not self.running:
            return

        self.success_label.configure(text="")

        self.root.after(
            1200,
            self.open_video_display
        )

    def open_video_display(self):

        if not self.running:
            return

        if self.connection_screen:
            self.connection_screen.destroy()
            self.connection_screen = None

        self.video_started = True

        self.video_canvas = tk.Canvas(
            self.content,
            bg="black",
            highlightthickness=0
        )
        self.video_canvas.pack(
            fill="both",
            expand=True
        )

        self.show_video_frames()

    # --------------------------------------------------------
    # VIDEO DISPLAY
    # --------------------------------------------------------

    def show_video_frames(self):

        if not self.running or not self.video_started:
            return

        try:
            frame = self.frames.get_nowait()

            canvas_width = max(
                self.video_canvas.winfo_width(),
                1
            )
            canvas_height = max(
                self.video_canvas.winfo_height(),
                1
            )

            image_width, image_height = frame.size

            scale = min(
                canvas_width / image_width,
                canvas_height / image_height
            )

            new_size = (
                max(1, int(image_width * scale)),
                max(1, int(image_height * scale))
            )

            frame = frame.resize(
                new_size,
                Image.Resampling.LANCZOS
            )

            self.current_photo = ImageTk.PhotoImage(frame)

            self.video_canvas.delete("all")

            self.video_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.current_photo,
                anchor="center"
            )

        except queue.Empty:
            pass

        except Exception:
            pass

        self.root.after(
            15,
            self.show_video_frames
        )

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    def process_events(self):

        if not self.running:
            return

        try:
            while True:

                event, data = self.events.get_nowait()

                if event == "connected":

                    self.status_label.configure(
                        text="Connected!",
                        text_color=GREEN
                    )

                    self.show_success(data)

                elif event == "error":

                    self.connected = False
                    self.video_started = False

                    if self.connection_screen:
                        self.connection_screen.destroy()
                        self.connection_screen = None

                    if self.video_canvas:
                        self.video_canvas.destroy()
                        self.video_canvas = None

                    if self.waiting_screen:
                        self.waiting_screen.pack(
                            fill="both",
                            expand=True
                        )

                    self.connect_button.configure(
                        text="Connect",
                        state="normal"
                    )

                    self.status_label.configure(
                        text="Connection failed. Try again.",
                        text_color=RED
                    )

                    messagebox.showerror(
                        "Karmy connection",
                        data
                    )

        except queue.Empty:
            pass

        self.root.after(
            30,
            self.process_events
        )

    # --------------------------------------------------------
    # WINDOW CONTROLS
    # --------------------------------------------------------

    def minimize_app(self):

        # Minimize the full-screen receiver.
        # Windows taskbar becomes accessible.
        self.root.iconify()

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    def exit_app(self):

        if not self.running:
            return

        self.running = False

        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass

            try:
                self.sock.close()
            except Exception:
                pass

        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = KarmyReceiver()
    app.run()
