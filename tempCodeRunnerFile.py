from tkinter import *
from tkinter import messagebox
from tkinter import filedialog as fd
import tkinter
from tkinter.tix import IMAGETEXT
from PIL import Image
import customtkinter
import os
import shutil
import pyrebase
import re
import time

# Default colour mode to system
customtkinter.set_appearance_mode("System") 
customtkinter.set_appearance_mode("dark-blue")

# Connect to firebase realtime database
config = {
    "databaseURL":"https://covertmark-92afe-default-rtdb.asia-southeast1.firebasedatabase.app/",
    "apiKey": "AIzaSyAMf-uHwELrHzzB6ChVDA0nDRDGKsAUAyk",
    "authDomain": "covertmark-92afe.firebaseapp.com",
    "projectId": "covertmark-92afe",
    "storageBucket": "covertmark-92afe.appspot.com",
    "messagingSenderId": "1018156024347",
    "appId": "1:1018156024347:web:9a634e0d001f80ed932ebe",
    "measurementId": "G-KK1E91LSVQ"
}

firebase = pyrebase.initialize_app(config)
database = firebase.database()
auth=firebase.auth()

class App(customtkinter.CTk):
    # Window resolution
    width = 1280
    height = 720
    currentframe = ""
    # Functionality Methods

    # User Authentication Module Methods
    def load(self):
        self.loadingscreen_frame.grid(row=0, column=0, sticky="nsew")
        self.loadingscreen_frame.grid_forget()

    def login_event(self):
        if self.logemail_entry.get() == '' or self.logpassword_entry.get() == '':
            messagebox.showerror('Error!','All fields are required')
        else:
            try:
                #self.login=auth.sign_in_with_email_and_password(self.logemail_entry.get(), self.logpassword_entry.get())
                #auth.send_email_verification(self.login['idToken'])
                #messagebox.showinfo('Success!','A verification email will be sent shortly.')
                self.login_frame.grid_forget()  # remove login frame
                self.navigation_frame.grid(row=0,column=0, sticky="ne")
                self.home_frame.grid(row=1,column=0, sticky="nsew")
            except:
                messagebox.showerror('Error!','Invalid email or password.')

    def logout_event(self):
        # Clear all frames before logging out
        self.home_frame.grid_forget()
        self.navigation_frame.grid_forget()
        self.embedding_frame.grid_forget()
        self.embedsummary_frame.grid_forget()
        self.management_frame.grid_forget()
        self.analysing_frame.grid_forget()
        self.login_frame.grid(row=0, column=0, sticky="nse")
        # Retain login details if remember me is checked
        if self.remember_checkbox.get() == 0:
            self.logemail_entry.delete(0, END)
            self.logpassword_entry.delete(0, END)

    def resetpass_event(self):
        # Open reset password frame
        self.login_frame.grid_forget()
        self.forgot_frame.grid(row=0, column=0, sticky="nse")

    def register_event(self):
        # Open register frame
        self.login_frame.grid_forget()
        self.register_frame.grid(row=0, column=0, sticky="nse")

    def signup_event(self):
        # Validate registration details
        if self.regemail_entry.get() == '' or self.regpassword_entry.get() == '' or self.regconfirmpass_entry.get() == '':
            messagebox.showerror('Error!','All fields are required')
        elif self.regpassword_entry.get() != self.regconfirmpass_entry.get():
            messagebox.showerror('Error!', 'Passwords do not match.')
        elif not self.validate_email(self.regemail_entry.get()):
            messagebox.showerror('Error!', 'Invalid email format.')
        elif not self.validate_password(self.regpassword_entry.get()):
            messagebox.showerror('Error!', 'Invalid password format.')
        elif self.toscheckbox.get() == 0:
            messagebox.showerror('Error!', 'Please accept the Terms & Conditions')
        else:
            # Create user in firebase database
            try:
                email = self.regemail_entry.get()
                password = self.regpassword_entry.get()
                auth.create_user_with_email_and_password(email, password)
                messagebox.showinfo('Success!','You have successfully registered.')
                self.register_frame.grid_forget()
                self.login_frame.grid(row=0, column=0, sticky="nse")
            except:
                messagebox.showerror('Error!', 'Email already exists!')

    # Validate email format using regular expression
    def validate_email(self, email):
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(email_regex, email) is not None

    # Validate password format using regular expression
    def validate_password(self, password):
        password_regex = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$'
        return re.match(password_regex, password) is not None
    
    # Send password reset email
    def send_button_event(self):
        try:
            auth.send_password_reset_email(self.forgemail_entry.get())
            messagebox.showinfo('Pending', 'Password reset email has been sent.')
            self.forgot_frame.grid_forget()
            self.login_frame.grid(row=0, column=0, sticky="nse")
        except:
            messagebox.showerror('Error!', 'Email does not exist')

    # Clear all fields in register frame
    def clear_button_event(self):
        self.regemail_entry.delete(0, END)
        self.regpassword_entry.delete(0, END)
        self.regconfirmpass_entry.delete(0, END)
        self.toscheckbox.deselect()

    # Return method for all back and cancel buttons
    def goback(self, backfrom):
        if backfrom == "Forget":
            self.forgot_frame.grid_forget()  # remove main frame
            self.login_frame.grid(row=0, column=0, sticky="nse")  # show login frame
        elif backfrom == "Register":
            self.register_frame.grid_forget()  # remove main frame
            self.login_frame.grid(row=0, column=0, sticky="nse")  # show login frame
        elif backfrom == "Embed":
            self.embedding_frame.grid_forget()
            self.navigate("Home")
        elif backfrom == "Embed Summary":
            self.embedsummary_frame.grid_forget()
            self.navigate("Embed")
        else:
            print("Error")


    # Return method for all back and cancel buttons
    def registerback_button_event(self):
        self.goback("Register")

    def forgotback_button_event(self):
        self.goback("Forget")

    def embedcancel_button_event(self):
        self.goback("Embed")

    def embedsumcancel_button_event(self):
        self.goback("Embed Summary")

    # Hide and unhide password mask
    def hide(self):
        self.close_eye_image.configure(image=self.close_eye_image)
        self.regpassword_entry.configure(show = '*')
        self.regconfirmpass_entry.configure(show = '*')
        self.hide_button.configure(command=self.unhide)

    def unhide(self):
        self.close_eye_image.configure(image=self.open_eye_image)
        self.regpassword_entry.configure(show = '')
        self.regconfirmpass_entry.configure(show = '')
        self.hide_button.configure(command=self.hide)

    # Main Menu Methods
    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def navigate(self, navoption):
        # Set button color for selected button
        self.navhome_button.configure(fg_color="transparent" if navoption == "Home" else "transparent")
        self.navembed_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Embed" else "transparent")
        self.navwatermarks_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Watermarks" else "transparent")
        self.navanalyse_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Analyse" else "transparent")

        # Show selected frame from navigation bar
        if navoption == "Home":
            self.home_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if navoption == "Embed":
            self.embedding_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.embedding_frame.grid_forget()
        if navoption == "Watermarks":
            self.management_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.management_frame.grid_forget()
        if navoption == "Analyse":
            self.analysing_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.analysing_frame.grid_forget()
        if navoption == "Profile":
            self.profile_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.profile_frame.grid_forget()
        if navoption == "Settings":
            self.settings_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.settings_frame.grid_forget()

    # Navigation Bar Methods
    def navhome_button_event(self):
        self.navigate("Home")

    def navembed_button_event(self):
        self.navigate("Embed")

    def navwatermarks_button_event(self):
        self.navigate("Watermarks")
    
    def navanalyse_button_event(self):
        self.navigate("Analyse")

    def navprofile_button_event(self):
        self.navigate("Profile")

    def navsettings_button_event(self):
        self.navigate("Settings")

    # Settings Methods
    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    
    def change_resolution_event(self, new_resolution: str):
        new_resolution = self.resolution_ddl.get()
        width, height = map(int, new_resolution.split('x'))
        self.geometry(f"{width}x{height}")

    # Watermark Embedding Module Methods

    # Open file explorer to select watermark image
    def browse_button_event(self):
        media_file = tkinter.filedialog.askopenfilename(filetypes = ([('png', '*.png'),('jpeg', '*.jpeg'),('jpg', '*.jpg'),('All Files', '*.*')]))
        if not media_file:
            messagebox.showerror('Error!', 'No image selected')
        else:
            media_image = Image.open(media_file)
            #change media preview image to uploaded image
            self.media_preview_image = IMAGETEXT.PhotoImage(media_image)
            


    # Open file explorer to save watermarked image to local storage
    def saveas_button_event(self):
        watermark_image = tkinter.filedialog.asksavefilename(filetypes = ([('png', '*.png'),('jpeg', '*.jpeg'),('jpg', '*.jpg'),('All Files', '*.*')]))

    # Open file explorer to select image to embed watermark into
    def embed_summary_event(self):
        self.embedding_frame.grid_forget()
        self.embedsummary_frame.grid(row=1, column=0, sticky="nsew")
    # Watermark Analysis Module Methods

    # Watermark Management Module Methods

    # Main Method
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure window settings
        self.title("CovertMark")
        #set the default resolution of the window to the selected resolution from self.resolution_ddl

        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)
        self.iconbitmap("Images/CovertMarkLogo.ico")

        # Images relative file paths
        # Backgrounds
        self.loginbg_image = customtkinter.CTkImage(Image.open("Images/LoginBG.png"), size=(880,720))
        self.forgotpwbg_image = customtkinter.CTkImage(Image.open("Images/ForgotPWBG.png"), size=(880,720))
        self.registerbg_image = customtkinter.CTkImage(Image.open("Images/RegisterBG.png"), size=(880,720))

        # Logo
        self.smalllogo_image = customtkinter.CTkImage(Image.open("Images/CovertMarkLogo.png"), size = (40,40))
        self.logo_image = customtkinter.CTkImage(Image.open("Images/CovertMarkLogo.png"), size = (200,200))

        # Icons
        self.close_eye_image = customtkinter.CTkImage(Image.open("Images/ClosedEye.png"))
        self.open_eye_image = customtkinter.CTkImage(Image.open("Images/OpenEye.png"))

        self.list_image = customtkinter.CTkImage(light_image=Image.open("Images/LightList.png"), dark_image=Image.open("Images/DarkList.png"), size=(20,20))
        self.analyse_image = customtkinter.CTkImage(light_image=Image.open("Images/LightAnalyse.png"), dark_image=Image.open("Images/DarkAnalyse.png"), size=(20,20))
        self.embed_image = customtkinter.CTkImage(light_image=Image.open("Images/LightEmbed.png"), dark_image=Image.open("Images/DarkEmbed.png"), size=(20,20))
        self.saveas_image = customtkinter.CTkImage(light_image=Image.open("Images/LightSave.png"), dark_image=Image.open("Images/DarkSave.png"), size=(20,20))
        self.browse_image = customtkinter.CTkImage(light_image=Image.open("Images/LightBrowse.png"), dark_image=Image.open("Images/DarkBrowse.png"), size=(20,20))
        self.profile_image = customtkinter.CTkImage(light_image=Image.open("Images/LightProfile.png"), dark_image=Image.open("Images/DarkProfile.png"), size=(20,20))
        self.settings_image = customtkinter.CTkImage(light_image=Image.open("Images/LightSettings.png"), dark_image=Image.open("Images/DarkSettings.png"), size=(20,20))
        self.logout_image = customtkinter.CTkImage(Image.open("Images/Logout.png"), size=(20,20))

        # Temporary Preview Images
        self.media_preview_image = customtkinter.CTkImage(Image.open("Images/ExamplePreview.jpg"), size=(500,500))
        self.watermark_preview_image = customtkinter.CTkImage(Image.open("Images/ExamplePreview.jpg"), size=(120,120))
        self.markedmedia_preview_image = customtkinter.CTkImage(Image.open("Images/ExamplePreview.jpg"), size=(350,350))

        # ------------------------------- Login frame ------------------------------- #

        self.login_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.login_frame.grid(row=0, column=0, sticky="nse")
        
        self.loginbg_image_label = customtkinter.CTkLabel(self.login_frame, image=self.loginbg_image, text="")
        self.loginbg_image_label.grid(row=0, column=0, rowspan=10)

        self.logo_image_label = customtkinter.CTkLabel(self.login_frame, image=self.logo_image, text="")
        self.logo_image_label.grid(row=0, column=1, pady=(80,0))

        self.login_label = customtkinter.CTkLabel(self.login_frame, text="Welcome to CovertMark", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.login_label.grid(row=1, column=1, padx=30, pady=(15, 15))
        
        # Entry Fields
        self.logemail_entry = customtkinter.CTkEntry(self.login_frame, width=200, placeholder_text="Email")
        self.logemail_entry.grid(row=2, column=1, padx=30, pady=(15, 5))

        self.logpassword_entry = customtkinter.CTkEntry(self.login_frame, width=200, show="*", placeholder_text="Password")
        self.logpassword_entry.grid(row=3, column=1, padx=30, pady=5)

        self.remember_checkbox = customtkinter.CTkCheckBox(self.login_frame, text="Remember Me")
        self.remember_checkbox.grid(row=4, column=1, padx=(100,0), pady=5, sticky="w")

        # Controls
        self.login_button = customtkinter.CTkButton(self.login_frame, text="Login", command=self.login_event, width=200)
        self.login_button.grid(row=5, column=1, padx=30, pady=5)

        self.reset_button = customtkinter.CTkButton(self.login_frame, text="Forgot password?", command=self.resetpass_event, width=200)
        self.reset_button.grid(row=6, column=1, padx=30, pady=(5, 15))

        self.signUpLabel = customtkinter.CTkLabel(self.login_frame, text='Not a member?')
        self.signUpLabel.grid(row=7, column=1, padx=30, pady=(35, 0))

        self.register_button = customtkinter.CTkButton(self.login_frame, text='Register Now', command=self.register_event, width=200)
        self.register_button.grid(row=8, column=1, padx=30, pady=(0, 15))
        
        self.appearance_mode = customtkinter.CTkOptionMenu(self.login_frame, values=["System", "Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode.grid(row=9, column=1, padx=20, pady=20, sticky="se")

        # ------------------------------- Register Frame ------------------------------- #

        self.register_frame = customtkinter.CTkFrame(self, corner_radius=0)

        self.registerbg_image_label = customtkinter.CTkLabel(self.register_frame, image=self.registerbg_image, text="")
        self.registerbg_image_label.grid(row=0, column=0, rowspan=10)

        self.register_label = customtkinter.CTkLabel(self.register_frame, text="Registration", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.register_label.grid(row=0, column=1, padx=115, pady=(50,15))

        # Entry Fields
        self.regemail_entry = customtkinter.CTkEntry(self.register_frame, width=200, placeholder_text="Email")
        self.regemail_entry.grid(row=1, column=1, padx=30, pady=5)

        self.regpassword_entry = customtkinter.CTkEntry(self.register_frame, width=200, show="*", placeholder_text="Password")
        self.regpassword_entry.grid(row=2, column=1, padx=30, pady=5)

        self.regconfirmpass_entry = customtkinter.CTkEntry(self.register_frame, width=200, show="*", placeholder_text="Confirm Password")
        self.regconfirmpass_entry.grid(row=3, column=1, padx=30, pady=5)

        # Controls
        self.hide_button = customtkinter.CTkButton(self.register_frame, text="", image=self.close_eye_image, command=self.unhide)
        self.hide_button.grid(row=4, column=1, padx=30, pady=(0, 15))

        self.toscheckbox = customtkinter.CTkCheckBox(self.register_frame, text="I Agree to the Terms & Conditions")
        self.toscheckbox.grid(row=5, column=1, padx=30, pady=(0,15))

        self.signup_button = customtkinter.CTkButton(self.register_frame, text="Sign Up", command=self.signup_event, width=200)
        self.signup_button.grid(row=6, column=1, padx=30, pady=(15, 15))

        self.clear_button = customtkinter.CTkButton(self.register_frame, text="Clear All", command=self.clear_button_event, width=200)
        self.clear_button.grid(row=7, column=1, padx=30, pady=(0, 15))

        self.back_button = customtkinter.CTkButton(self.register_frame, text="Back", command=self.registerback_button_event, width=200)
        self.back_button.grid(row=8, column=1, padx=30, pady=(0, 15))

        self.appearance_mode = customtkinter.CTkOptionMenu(self.register_frame, values=["System", "Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode.grid(row=9, column=1, padx=20, pady=(110, 20), sticky="se")

        # ------------------------------- Forgot Password Frame ------------------------------- #

        self.forgot_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.forgot_label = customtkinter.CTkLabel(self.forgot_frame, text="Forgot Password",
                                                 font=customtkinter.CTkFont(size=30, weight="bold"))
        self.forgot_label.grid(row=0, column=1, padx=80, pady=(150, 15))

        self.forgotpwbg_image_label = customtkinter.CTkLabel(self.forgot_frame, image=self.forgotpwbg_image, text="")
        self.forgotpwbg_image_label.grid(row=0, column=0, rowspan=5)

        # Entry Fields
        self.forgemail_entry = customtkinter.CTkEntry(self.forgot_frame, width=200, placeholder_text="Email")
        self.forgemail_entry.grid(row=1, column=1, padx=30, pady=(15, 15))

        # Controls
        self.send_button = customtkinter.CTkButton(self.forgot_frame, text="Send Verification Code", command=self.send_button_event, width=200)
        self.send_button.grid(row=2, column=1, padx=30, pady=(0, 15))

        self.back_button = customtkinter.CTkButton(self.forgot_frame, text="Back", command=self.forgotback_button_event, width=200)
        self.back_button.grid(row=3, column=1, padx=30, pady=(0, 15))

        self.appearance_mode = customtkinter.CTkOptionMenu(self.forgot_frame, values=["System", "Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode.grid(row=4, column=1, padx=20, pady=(320, 20), sticky="se")

        # ------------------------------- Navigation frame ------------------------------- #

        # Navigation Bar
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color=("sky blue", "steel blue"))
        self.navigation_frame.grid_columnconfigure(4, weight=1)

        self.navhome_button = customtkinter.CTkButton(self.navigation_frame, text="CovertMark", font=customtkinter.CTkFont(size=24, weight="bold"), width=75, border_spacing=10, fg_color="transparent", text_color=("black", "white"), hover_color=("sky blue", "steel blue"), image=self.smalllogo_image, command=self.navhome_button_event)
        self.navhome_button.grid(row=0, column=0, padx=10, sticky="w")

        self.appearance_mode = customtkinter.CTkOptionMenu(self.navigation_frame, values=["System", "Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode.grid(row=0, column=1, padx=(10, 250), sticky="w")

        self.navembed_button = customtkinter.CTkButton(self.navigation_frame, text="Embed", width=75, border_spacing=10, fg_color="transparent", text_color=("black", "white"), hover_color=("alice blue", "DodgerBlue4"), image=self.embed_image, command=self.navembed_button_event)
        self.navembed_button.grid(row=0, column=2, padx=10,sticky="e")

        self.navwatermarks_button = customtkinter.CTkButton(self.navigation_frame, text="Watermarks", width=75, border_spacing=10, fg_color="transparent", text_color=("black", "white"), hover_color=("alice blue", "DodgerBlue4"), image=self.list_image, command=self.navwatermarks_button_event)
        self.navwatermarks_button.grid(row=0, column=3, padx=10,sticky="e")

        self.navanalyse_button = customtkinter.CTkButton(self.navigation_frame, text="Analyse", width=75, border_spacing=10, fg_color="transparent", text_color=("black", "white"), hover_color=("alice blue", "DodgerBlue4"), image=self.analyse_image, command=self.navanalyse_button_event)
        self.navanalyse_button.grid(row=0, column=4, padx=10,sticky="e")

        self.profile_button = customtkinter.CTkButton(self.navigation_frame, text="", width=75, border_spacing=10, fg_color="transparent", text_color=("black", "white"), hover_color=("alice blue", "DodgerBlue4"), image=self.profile_image, command=self.navprofile_button_event)
        self.profile_button.grid(row=0, column=5, padx=10,sticky="e")

        self.settings_button = customtkinter.CTkButton(self.navigation_frame, text="", width=75, border_spacing=10, fg_color="transparent", text_color=("black", "white"), hover_color=("alice blue", "DodgerBlue4"), image=self.settings_image, command=self.navsettings_button_event)
        self.settings_button.grid(row=0, column=6, padx=10,sticky="e")

        self.logout_button = customtkinter.CTkButton(self.navigation_frame, text="", command=self.logout_event, width=75, border_spacing=10, fg_color="transparent", text_color=("black", "white"), hover_color=("alice blue", "DodgerBlue4"), image=self.logout_image)
        self.logout_button.grid(row=0, column=7, padx=10,sticky="e")

        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_rowconfigure(0, weight=1)
        self.home_label = customtkinter.CTkLabel(self.home_frame, text="Home Page",)
        self.home_label.grid(row=1, column=0, padx=20, pady=10)

        # ------------------------------- Watermark Embedding Frame ------------------------------- #
        # Left side
        self.embedding_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.embedding_label = customtkinter.CTkLabel(self.embedding_frame, text="Watermark Embedding", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.embedding_label.grid(row=0, column=0, padx=30, pady=20, sticky="w", columnspan=2)

        self.insert_media_label = customtkinter.CTkLabel(self.embedding_frame, text="Insert Media File")
        self.insert_media_label.grid(row=1, column=0, padx=30, pady=(15,5), sticky="w")

        self.browse_button = customtkinter.CTkButton(self.embedding_frame, text="Browse Files",image=self.browse_image, command=self.browse_button_event, width=120)
        self.browse_button.grid(row=2, column=0, padx=30, pady=(5, 15), sticky="w")

        self.insert_watermark_label = customtkinter.CTkLabel(self.embedding_frame, text="Insert Watermark File")
        self.insert_watermark_label.grid(row=3, column=0, padx=30, pady=(15,5), sticky="w")

        self.browse_button = customtkinter.CTkButton(self.embedding_frame, text="Browse Files",image=self.browse_image, command=self.browse_button_event, width=120)
        self.browse_button.grid(row=4, column=0, padx=30, pady=(5, 15), sticky="w")

        self.watermark_preview_label = customtkinter.CTkLabel(self.embedding_frame, text="Watermark Preview")
        self.watermark_preview_label.grid(row=5, column=0, padx=30, pady=(20,0), sticky="w")

        self.watermark_image_label = customtkinter.CTkLabel(self.embedding_frame, text="", image=self.watermark_preview_image)
        self.watermark_image_label.grid(row=6, column=0, padx=30, pady=(0,25), sticky="w", columnspan=2)

        self.technique_label = customtkinter.CTkLabel(self.embedding_frame, text="Steganography Technique")
        self.technique_label.grid(row=7, column=0, padx=30, pady=(25,5), sticky="w", rowspan= 2, columnspan=2)

        self.technique_var = tkinter.IntVar(value=0)
        self.ss_radiobutton = customtkinter.CTkRadioButton(self.embedding_frame, variable=self.technique_var, value = 0, text="Spread Spectrum")
        self.ss_radiobutton.grid(row=9, column=0, padx=(30,5), pady=(5,20), sticky="w")
        self.dwt_radiobutton = customtkinter.CTkRadioButton(self.embedding_frame, variable=self.technique_var, value = 1, text="Discrete Wavelet Transform")
        self.dwt_radiobutton.grid(row=9, column=1, padx=(5,30), pady=(5,20), sticky="w")

        self.continue_button = customtkinter.CTkButton(self.embedding_frame, text="Continue", width=120 , command=self.embed_summary_event)
        self.continue_button.grid(row=10, column=0, padx=(30,0), pady=(5, 15), sticky="w")

        self.cancel_button = customtkinter.CTkButton(self.embedding_frame, text="Cancel", width=120, fg_color="red", text_color="white", command=self.embedcancel_button_event)
        self.cancel_button.grid(row=10, column=1, padx=(0,30), pady=(5, 15), sticky="w")

        self.empty1_label = customtkinter.CTkLabel(self.embedding_frame, text="")
        self.empty1_label.grid(row=11, column=0, padx=30, pady=10)

        # Right side
        self.media_preview_label = customtkinter.CTkLabel(self.embedding_frame, text="Media File Preview")
        self.media_preview_label.grid(row=0, column=2, padx=30, pady=(15,5), sticky="w")

        self.media_image_label = customtkinter.CTkLabel(self.embedding_frame, text="", image=self.media_preview_image)
        self.media_image_label.grid(row=1, column=2, padx=30, pady=(5,15), sticky="w", rowspan=11)

        # ------------------------------- Watermark Embedding Summary Frame ------------------------------- #

        self.embedsummary_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.embedsummary_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Embedding Summary", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.embedsummary_label.grid(row=0, column=0, padx=30, pady=20, sticky="w", columnspan=2)
        
        self.author_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Author\t\t\t:")
        self.author_label.grid(row=1, column=0, padx=30,pady=(15,5), sticky="w")
        
        self.wmID_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Watermark ID\t\t:")
        self.wmID_label.grid(row=2, column=0, padx=30, sticky="w")

        self.mediafile_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Media File\t\t:")
        self.mediafile_label.grid(row=3, column=0, padx=30, sticky="w")

        self.watermarkfile_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Watermark File\t\t:")
        self.watermarkfile_label.grid(row=4, column=0, padx=30, sticky="w")

        self.embeddate_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Date\t\t\t:")
        self.embeddate_label.grid(row=5, column=0, padx=30, sticky="w")

        self.techniqueused_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Steagography Technique\t:")
        self.techniqueused_label.grid(row=6, column=0, padx=30, sticky="w")

        self.saveas_button = customtkinter.CTkButton(self.embedsummary_frame, text="Save As", width=120, image=self.saveas_image, command=self.saveas_button_event)
        self.saveas_button.grid(row=7, column=0, padx=(30,0), pady=(5, 15), sticky="w")

        self.embedsumcancel_button = customtkinter.CTkButton(self.embedsummary_frame, text="Back", width=120, fg_color="red", text_color="white", command=self.embedsumcancel_button_event)
        self.embedsumcancel_button.grid(row=7, column=1, padx=(0,30), pady=(5, 15), sticky="w")

        # Middle
        self.markedmedia_preview_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Watermarked Media File Preview")
        self.markedmedia_preview_label.grid(row=0, column=2, padx=30, pady=(15,5), sticky="w")

        self.before_preview_label = customtkinter.CTkLabel(self.embedsummary_frame, text="Before")
        self.before_preview_label.grid(row=1, column=2, padx=30, pady=(15,5), sticky="w")

        self.markedmedia_image_label = customtkinter.CTkLabel(self.embedsummary_frame, text="", image=self.markedmedia_preview_image)
        self.markedmedia_image_label.grid(row=2, column=2, padx=30, pady=(5,15), sticky="w", rowspan=7)

        # Right side
        self.after_preview_label = customtkinter.CTkLabel(self.embedsummary_frame, text="After")
        self.after_preview_label.grid(row=1, column=3, padx=30, pady=(15,5), sticky="w")

        self.markedmedia_image_label = customtkinter.CTkLabel(self.embedsummary_frame, text="", image=self.markedmedia_preview_image)
        self.markedmedia_image_label.grid(row=2, column=3, padx=30, pady=(5,15), sticky="w", rowspan=7)






        # ------------------------------- Watermark Analysis Module Frame ------------------------------- #
        self.analysing_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.analysing_label = customtkinter.CTkLabel(self.analysing_frame, text="Analysing Module")
        self.analysing_label.grid(row=1, column=0, padx=20, pady=10)

        # ------------------------------- Watermark Management Module Frame ------------------------------- #
        self.management_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.management_label = customtkinter.CTkLabel(self.management_frame, text="Management Module")
        self.management_label.grid(row=1, column=0, padx=20, pady=10)

        # Loading Screen
        self.loadingscreen_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.loadingscreen_label = customtkinter.CTkLabel(self.loadingscreen_frame, text="Loading")
        self.loadingscreen_label.grid(row=0, column=0, sticky="nsew")


        # ------------------------------- Profile Frame ------------------------------- #
        self.profile_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.profile_label = customtkinter.CTkLabel(self.profile_frame, text="Profile")
        self.profile_label.grid(row=0, column=0, padx=20, pady=10)
        


        # ------------------------------- Settings Frame ------------------------------- #
        self.settings_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.settings_label = customtkinter.CTkLabel(self.settings_frame, text="Settings")
        self.settings_label.grid(row=0, column=0, padx=20, pady=10)
        
        self.resolution_label = customtkinter.CTkLabel(self.settings_frame, text="Resolution")
        self.resolution_label.grid(row=1, column=0, padx=20, pady=10)
        self.resolution_list = ["1920x1080", "1280x720", "1024x768", "800x600"]
        self.resolution_ddl = customtkinter.CTkComboBox(self.settings_frame, values=self.resolution_list, width=20, command=self.change_resolution_event)
        self.resolution_ddl.grid(row=1, column=1, padx=20, pady=10)

        #create a combobox for ui scaling
        self.uiscaling_label = customtkinter.CTkLabel(self.settings_frame, text="UI Scaling")
        self.uiscaling_label.grid(row=2, column=0, padx=20, pady=10)
        self.uiscaling_list = ["80%", "90%", "100%", "110%", "120%"]
        self.uiscaling_ddl = customtkinter.CTkComboBox(self.settings_frame, values=self.uiscaling_list, width=20, command=self.change_scaling_event)
        self.uiscaling_ddl.grid(row=2, column=1, padx=20, pady=10)


        # Default Settings
        self.navigate("Home")
        self.resolution_ddl.set("1920x1080")
        self.uiscaling_ddl.set("100%")

if __name__ == "__main__":
    app = App()
    app.mainloop()