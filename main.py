import datetime
import itertools
import customtkinter
import os
import cv2
import numpy as np
import pyrebase
import re
import uuid
import tkinter
import matplotlib.pyplot as plt
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter.tix import IMAGETEXT
from PIL import Image
from pathlib import Path


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
auth = firebase.auth()
#storage = firebase.storage()

quant = np.array([[16,11,10,16,24,40,51,61],      # QUANTIZATION TABLE
                    [12,12,14,19,26,58,60,55],    # required for DCT
                    [14,13,16,24,40,57,69,56],
                    [14,17,22,29,51,87,80,62],
                    [18,22,37,56,68,109,103,77],
                    [24,35,55,64,81,104,113,92],
                    [49,64,78,87,103,121,120,101],
                    [72,92,95,98,112,100,103,99]])

class App(customtkinter.CTk):
    # Window resolution
    width = 1280
    height = 720
    
    # Functionality Methods

    # User Authentication Module Methods
    def load(self):
        #display the loading screen for 3 seconds
        self.loading_frame.grid(row=0, column=0, sticky="nsew")
        self.after(1500, self.loading_frame.grid_forget)

    def login_event(self):
        if self.logemail_entry.get() == '' or self.logpassword_entry.get() == '':
            self.invalid_login_label.configure(text="All fields are required.")
        else:
            try:
                # Login user with email and password
                self.user_login=auth.sign_in_with_email_and_password(self.logemail_entry.get(), self.logpassword_entry.get())
                # Check if email is verified
                user_data = auth.get_account_info(self.user_login['idToken'])
                email_verified = user_data['users'][0]['emailVerified']
                user_details = database.child("users").child(self.user_login['localId']).get(self.user_login['idToken']).val()
                user_email = user_details.get('email')
                if email_verified == False:
                    self.invalid_login_label.configure(text= "Please verify your email first.")
                    auth.send_email_verification(self.user_login['idToken'])
                else:
                    self.login_frame.grid_forget()
                    self.load()
                    self.navigation_frame.grid(row=0,column=0, sticky="ne")
                    self.home_frame.grid(row=1,column=0, sticky="nsew")
                    #Obtain user details from database
                    self.user_email = user_details.get('email')
                    self.user_name = user_details.get('name')
                    self.user_organisation = user_details.get('organisation')
                    #Set the email in profile to the user's email
                    self.profile_email_entry.configure(placeholder_text="" + user_email)
                    self.name_entry.configure(placeholder_text="" + self.user_name)
                    self.org_entry.configure(placeholder_text="" + self.user_organisation)
                       
            except Exception as error:
                print(error)
                self.invalid_login_label.configure(text="Invalid email or password.")

    def logout_event(self):
        # Clear all frames before logging out
        self.home_frame.grid_forget()
        self.navigation_frame.grid_forget()
        self.encoding_frame.grid_forget()
        self.management_frame.grid_forget()
        self.decoding_frame.grid_forget()
        self.profile_frame.grid_forget()
        self.settings_frame.grid_forget()

        self.login_frame.grid(row=0, column=0, sticky="nse")
        self.load()
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
            self.signuperror_label.configure(text="All fields are required.")
        elif self.regpassword_entry.get() != self.regconfirmpass_entry.get():
            self.invalid_confirmpass_label.configure(text="Must match password.")
            self.signuperror_label.configure(text="Passwords do not match.")
        elif not self.validate_email(self.regemail_entry.get()):
            self.invalid_email_label.configure(text="Must be a valid email address.")
            self.signuperror_label.configure(text="Invalid email format.")
        elif not self.validate_password(self.regpassword_entry.get()):
            self.invalid_password_label.configure(text="Must be at least 8 characters long, contain at least\n1 uppercase letter, 1 lowercase letter and 1 number.")
            self.signuperror_label.configure(text="Invalid password format.")
        elif self.toscheckbox.get() == 0:
            self.signuperror_label.configure(text="Please accept the Terms & Conditions")
        else:
            # Create user in firebase database
            try:
                email = self.regemail_entry.get()
                password = self.regpassword_entry.get()
                new_user = auth.create_user_with_email_and_password(email, password)
                messagebox.showinfo('Success!','You have successfully registered. A verification email will be sent shortly.')
                try:
                    auth.send_email_verification(new_user['idToken'])
                except:
                    messagebox.showerror('Error!','Verification email could not be sent.')
                # add user details to database
                data = {"email": email, "name": "", "organisation": ""}
                database.child("users").child(new_user['localId']).set(data, new_user['idToken'])
                self.register_frame.grid_forget()
                self.load()
                self.login_frame.grid(row=0, column=0, sticky="nse")
            except:
                self.invalid_email_label.configure(text="Email already exists.")


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
            self.invalid_forgotpw_label.configure(text="Email does not exist.")

    def send2_button_event(self):
        try:
            auth.send_password_reset_email(self.forgemail_entry.get())
            messagebox.showinfo('Pending', 'Password reset email has been sent.')
            self.forgot_frame.grid_forget()
        except:
            self.invalid_forgotpw_label.configure(text="Email does not exist.")

    def sendchangepw_event(self):
        self.forgot_frame2.grid(row=0, column=0, sticky="nsew")
        
    # Clear all fields in register frame
    def clear_button_event(self):
        self.regemail_entry.delete(0, END)
        self.regpassword_entry.delete(0, END)
        self.regconfirmpass_entry.delete(0, END)
        self.toscheckbox.deselect()
        # Clear all error messages
        self.invalid_email_label.configure(text="")
        self.invalid_password_label.configure(text="")
        self.invalid_confirmpass_label.configure(text="")
        self.signuperror_label.configure(text="")
        # Reset hide button to closed eye
        self.hide_button.configure(image=self.close_eye_image, command=self.unhide)

    def open_tos(self):
        # open a scrollable new window to display the terms and conditions
        self.tos_window = Toplevel(self)
        self.tos_window.title("Terms & Conditions")
        self.tos_window.geometry("500x500")
        self.tos_window.resizable(False, False)
        self.tos_window.iconbitmap("Images/CovertMarkLogo.ico")
        self.tos_window.configure(bg="white")
        self.textbox = customtkinter.CTkTextbox(self.tos_window, width=500, height=500, bg_color="white", fg_color="black", font=customtkinter.CTkFont(size=10))
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.insert("0.0", "Terms & Conditions\n\n" + "By using the CovertMark Digital Steganography Watermark Application, you agree to the following terms and conditions:\n1. Intellectual Property: The Application, including all software, algorithms, and content, is the intellectual property of CovertMark, and is protected by copyright and other intellectual property laws. You may not copy, modify, distribute, or reverse engineer any part of the Application without the explicit written permission of CovertMark.\n\n2.Watermarking Usage: The Application is intended for lawful use only. You agree not to use the Application for any illegal, unethical, or unauthorized purposes, including but not limited to copyright infringement, data manipulation, or unauthorized access to digital media.\n\n3. Data Privacy: The Application may require access to certain data on your device to function properly. CovertMark will not collect or store any personal data without your explicit consent. We respect your privacy and adhere to all applicable data protection laws.\n\n4. Limited Warranty: The Application is provided as is without any warranties or guarantees. CovertMark makes no representations or warranties regarding the accuracy, reliability, or suitability of the Application for any specific purpose. You agree to use the Application at your own risk.\n\n5. Liability: CovertMark shall not be liable for any damages, including but not limited to direct, indirect, incidental, or consequential damages, arising from the use or inability to use the Application, even if CovertMark has been advised of the possibility of such damages.\n\n6. Updates and Support: CovertMark may release updates or new versions of the Application from time to time. While we strive to provide ongoing support, CovertMark reserves the right to discontinue support for older versions of the Application.\n\n7. Termination: CovertMark may terminate your access to and use of the Application at any time, without prior notice, if you violate these terms and conditions.\n\n8. Governing Law: These terms and conditions shall be governed by and construed in accordance with the laws of [Your Country/Region]. Any disputes arising from the use of the Application shall be subject to the exclusive jurisdiction of the courts in [Your Country/Region].\nBy installing and using the CovertMark Digital Steganography Watermark Application, you acknowledge that you have read, understood, and agree to these terms and conditions. If you do not agree with any part of these terms, please refrain from using the Application.\n\n" + "Last updated: 21 July 2023")

    def open_privacy(self):
        self.privacy_window = Toplevel(self)
        self.privacy_window.title("Privacy Policy")
        self.privacy_window.geometry("500x500")
        self.privacy_window.resizable(False, False)
        self.privacy_window.iconbitmap("Images/CovertMarkLogo.ico")
        self.privacy_window.configure(bg="white")
        self.textbox = customtkinter.CTkTextbox(self.privacy_window, width=500, height=500, bg_color="white", fg_color="black", font=customtkinter.CTkFont(size=10))
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.insert("0.0", "Privacy Policy\n\nEffective date: 21 July 2023\n\nIntroduction\n\nCovertMark Digital Steganography Watermark Application is committed to protecting your privacy. This Privacy Policy outlines the types of information we collect, how we use and protect that information, and your rights regarding your personal data. By using the CovertMark Digital Steganography Watermark Application, you consent to the terms and practices described in this Privacy Policy.\n\nInformation Collection and Use\n\nWe may collect personal information that you voluntarily provide while using the CovertMark Digital Steganography Watermark Application. This information may include your name, email address, and any other details you choose to share with us.\n\nWe may use the collected information to:\n\nProvide and maintain the functionality of the application.\nRespond to your requests, inquiries, or feedback.\nSend you important updates, newsletters, and notifications related to the application.\nImprove and optimize the application's performance and user experience.\n\nInformation Security\n\nWe are committed to ensuring the security of your personal information. However, please note that no method of transmission over the internet or electronic storage is entirely secure. While we strive to use commercially acceptable means to protect your personal data, we cannot guarantee its absolute security.\n\nData Sharing and Disclosure\n\nWe do not share or disclose your personal information to third parties except in the following circumstances:\n\nWith your explicit consent.\nIf required by law or to comply with legal processes.\nTo protect our rights, privacy, safety, or property.\n\nData Retention\n\nWe will retain your personal information only for as long as necessary to fulfill the purposes outlined in this Privacy Policy and as required by law.\n\nYour Rights\n\nYou have the right to access, correct, or delete your personal information stored in the CovertMark Digital Steganography Watermark Application. If you wish to exercise any of these rights, please contact me at edwin9938@gmail.com.\n\nChanges to this Privacy Policy\n\nWe reserve the right to update or modify this Privacy Policy at any time. Any changes will be effective upon posting the revised version on the CovertMark Digital Steganography Watermark Application website.\n\nContact Us\n\nIf you have any questions or concerns about this Privacy Policy or the CovertMark Digital Steganography Watermark Application's privacy practices, please contact me at edwin9938@gmail.com.")
        
    # Return method for all back and cancel buttons
    def goback(self, backfrom):
        if backfrom == "Forget":
            self.forgot_frame.grid_forget()
            self.login_frame.grid(row=0, column=0, sticky="nse")
        elif backfrom == "Register":
            self.register_frame.grid_forget()
            self.login_frame.grid(row=0, column=0, sticky="nse")
        elif backfrom == "Embed":
            self.encoding_frame.grid_forget()
            self.navigate("Home")
        elif backfrom == "LSB Encoding":
            self.lsb_encode_frame.grid_forget()
            self.navigate("Embed")
        elif backfrom == "LSB Decoding":
            self.lsb_decode_frame.grid_forget()
            self.navigate("Analyse")
        elif backfrom == "DCT Encoding":
            self.dct_encode_frame.grid_forget()
            self.navigate("Embed")
        elif backfrom == "DCT Decoding":
            self.dct_decode_frame.grid_forget()
            self.navigate("Analyse")
        elif backfrom == "Profile":
            self.forgot_frame2.grid_forget()
            self.navigate("Profile")
        else:
            print("Error")


    # Return method for all back and cancel buttons
    def registerback_button_event(self):
        self.goback("Register")

    def forgotback_button_event(self):
        self.goback("Forget")

    def embedcancel_button_event(self):
        self.goback("Embed")

    def lsb_encodecancel_button_event(self):
        self.goback("LSB Encoding")

    def lsb_decodecancel_button_event(self):
        self.goback("LSB Decoding")

    def dct_encodecancel_button_event(self):
        self.goback("DCT Encoding")

    def dct_decodecancel_button_event(self):
        self.goback("DCT Decoding") 
    
    def changeback_button_event(self):
        self.goback("Profile")

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

    def forget_all(self):
        #forget all frames
        self.home_frame.grid_forget()
        self.encoding_frame.grid_forget()
        self.lsb_encode_frame.grid_forget()
        self.lsb_decode_frame.grid_forget()
        self.decoding_frame.grid_forget()
        self.dct_encode_frame.grid_forget()
        self.dct_decode_frame.grid_forget()
        self.management_frame.grid_forget()
        self.profile_frame.grid_forget()
        self.settings_frame.grid_forget()

    def navigate(self, navoption):
        # Set button color for selected button
        self.navhome_button.configure(fg_color="transparent" if navoption == "Home" else "transparent")
        self.navembed_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Embed" else "transparent")
        self.navwatermarks_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Watermarks" else "transparent")
        self.navanalyse_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Analyse" else "transparent")
        self.profile_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Profile" else "transparent")
        self.settings_button.configure(fg_color=("alice blue", "DodgerBlue4") if navoption == "Settings" else "transparent")

        # Show selected frame from navigation bar
        if navoption == "Home":
            self.forget_all()
            self.home_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if navoption == "Embed":
            self.forget_all()
            self.encoding_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.encoding_frame.grid_forget()
        if navoption == "Watermarks":
            self.forget_all()
            self.management_frame.grid(row=1, column=0, sticky="nsew")
            self.treeview_frame.delete(*self.treeview_frame.get_children())
            self.ref = database.child("watermarks").order_by_child("owner").equal_to(self.user_login['localId']).get(self.user_login['idToken']).val()
            for ref in self.ref:
                self.treeview_frame.insert("", "end", text=ref, values=(self.ref[ref]['name'], self.ref[ref]['technique'], self.ref[ref]['size'], self.ref[ref]['date']))
        else:
            self.management_frame.grid_forget()
        if navoption == "Analyse":
            self.forget_all()
            self.decoding_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.decoding_frame.grid_forget()
        if navoption == "Profile":
            self.forget_all()
            self.profile_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.profile_frame.grid_forget()
        if navoption == "Settings":
            self.forget_all()
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

    # Profile Methods
    def cancel_changes_event(self):
            self.name_entry.delete(0, END)
            self.profile_email_entry.delete(0, END)
            self.org_entry.delete(0, END)

    def save_changes_event(self):
        if messagebox.askyesno("Save Changes", "Are you sure you want to save your changes?"):
            database.child('users').child(self.user_login['localId']).update({"name": self.name_entry.get(), "organisation": self.org_entry.get()}, self.user_login['idToken'])
            messagebox.showinfo("Success", "Your changes have been saved.")
            self.navigate("Home")

    def delete_account_event(self):
        if messagebox.askyesno("Delete Account", "Are you sure you want to delete your account?"):
            database.child('users').child(self.user_login['localId']).remove(self.user_login['idToken'])
            auth.delete_user_account(self.user_login['idToken'])
            messagebox.showinfo("Success", "Your account has been deleted.")
            self.logout_event()
    
    # Settings Methods
    def change_resolution_event(self, new_resolution: str):
        new_resolution = self.resolution_ddl.get()
        width, height = map(int, new_resolution.split('x'))
        if new_resolution == "1920x1080":
            new_scaling_float = 1.5
        elif new_resolution == "1600x900":
            new_scaling_float = 1.25
        elif new_resolution == "1280x720":
            new_scaling_float = 1
        else:
            new_scaling_float = 1
        self.geometry(f"{width}x{height}")
        customtkinter.set_widget_scaling(new_scaling_float)

    def change_display_event(self, new_display: str):
        new_display = self.display_ddl.get()

        if new_display == "Fullscreen" and not self.is_fullscreen:
            # Store the current resolution before entering fullscreen mode
            self.previous_resolution = self.resolution_ddl.get()

            # Set the resolution to 1920x1080 when entering fullscreen mode
            self.resolution_ddl.set("1920x1080")
            self.resolution_ddl.configure(state="disabled")
            self.change_resolution_event("1920x1080")

            # Enable fullscreen mode
            self.attributes("-fullscreen", True)
            self.is_fullscreen = True

        elif new_display != "Fullscreen" and self.is_fullscreen:
            # Restore the original resolution when exiting fullscreen mode
            if self.previous_resolution:
                self.resolution_ddl.set(self.previous_resolution)
                self.change_resolution_event(self.previous_resolution)
                self.resolution_ddl.configure(state="normal")

            # Disable fullscreen mode
            self.attributes("-fullscreen", False)
            self.is_fullscreen = False

    # Watermark Encoding Module Methods
    def lsb_encode_button_event(self):
        self.uploaded_file = tkinter.filedialog.askopenfilename(filetypes = ([('.png', '*.png'),('.jpeg', '*.jpeg'),('.jpg', '*.jpg')]))
        if not self.uploaded_file:
            messagebox.showerror("Error","You have selected nothing !")
        else:
            self.myimg = Image.open(self.uploaded_file)
            self.myimage = self.myimg.resize((400,400))
            self.img = customtkinter.CTkImage(self.myimage, size=(400,400))
            #create a frame for lsb encoding
            self.lsb_encode_frame.grid(row=1, column=0, sticky="nsew")

            #create a label for the frame
            self.lsb_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="LSB Encoding", font=customtkinter.CTkFont(size=30, weight="bold"))
            self.lsb_label.grid(row=0, column=0, padx=50, pady=30, columnspan=2, sticky='e')

            self.selected_image_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="Selected Image:", font=customtkinter.CTkFont(size=24, weight="bold"))
            self.selected_image_label.grid(row=1, column=0, padx=30, pady=0, sticky="w")

            self.lsb_image_label = customtkinter.CTkLabel(self.lsb_encode_frame, image=self.img, text="")
            self.lsb_image_label.grid(row=2, column=0, padx=30, pady=15, rowspan=10)
      
            self.lsb_image_name_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="Image Name: " + os.path.basename(self.uploaded_file))
            self.lsb_image_name_label.grid(row=2, column=1, padx=30, pady=0, sticky="w")
        
            self.lsb_image_size_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="Image Size: " + str(os.path.getsize(self.uploaded_file)) + " bytes")
            self.lsb_image_size_label.grid(row=3, column=1, padx=30, pady=0, sticky="w")
           
            self.lsb_image_resolution_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="Image Resolution: " + str(self.myimg.size[0]) + " x " + str(self.myimg.size[1]))
            self.lsb_image_resolution_label.grid(row=4, column=1, padx=30, pady=0, sticky="w")

            self.lsb_image_type_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="Image Type: " + self.myimg.format)
            self.lsb_image_type_label.grid(row=5, column=1, padx=30, pady=0, sticky="w")

            self.lsb_image_path_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="Image Path: " + self.uploaded_file)
            self.lsb_image_path_label.grid(row=6, column=1, padx=30, pady=0, sticky="w", columnspan=2)
            
            self.lsb_secret_message_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="Secret Message: ")
            self.lsb_secret_message_label.grid(row=7, column=1, padx=30, pady=0, sticky="w")

            self.lsb_secret_message_textbox = customtkinter.CTkTextbox(self.lsb_encode_frame, width=400, height=50, font=customtkinter.CTkFont(size=12))
            self.lsb_secret_message_textbox.grid(row=8, column=1, padx=30, pady=0, sticky="w", columnspan=2)
            
            #error label for the secret message
            self.lsb_secret_message_error_label = customtkinter.CTkLabel(self.lsb_encode_frame, text="")
            self.lsb_secret_message_error_label.grid(row=9, column=1, padx=0, pady=0, sticky="w")

            self.lsb_embed_button = customtkinter.CTkButton(self.lsb_encode_frame, text="Embed", command=self.lsb_embed_button_event, width=200)
            self.lsb_embed_button.grid(row=10, column=1, padx=10, pady=0)

            self.lsb_cancel_button = customtkinter.CTkButton(self.lsb_encode_frame, text="Cancel", command=self.lsb_encodecancel_button_event , width=200, fg_color="red", text_color="white")
            self.lsb_cancel_button.grid(row=10, column=2, padx=10, pady=0)
            # Generate unique id for the watermark
            self.watermark_id = str(uuid.uuid4())
            self.watermark_data = {"owner": self.user_login['localId'] ,"name": os.path.basename(self.uploaded_file), "size": str(os.path.getsize(self.uploaded_file)), "technique": "LSB", "date": str(datetime.datetime.now())}

    def lsb_embed_button_event(self):
        myimg = self.myimg
        if self.lsb_secret_message_textbox.get("1.0",END) == "":
            self.lsb_secret_message_error_label.configure(text="Enter your secret message!")
        else:
            data = self.lsb_secret_message_textbox.get("1.0",END)
            newimg = myimg.copy()
            self.encode_enc(newimg, data)
            temp=os.path.splitext(os.path.basename(myimg.filename))[0]
            try:
                newimg.save(tkinter.filedialog.asksaveasfilename(initialfile=temp,filetypes = ([('.png', '*.png'),('.jpeg', '*.jpeg'),('.jpg', '*.jpg')]),defaultextension=".png"))
                self.load()
                messagebox.showinfo("Success","Encoding Successful\nFile is encoded and saved in the selected directory")
                database.child("watermarks").child(self.watermark_id).set(self.watermark_data, self.user_login['idToken'])
                self.lsb_encode_frame.grid_forget()
            except:
                messagebox.showerror("Error","File is not saved")

    def encode_enc(self,newimg, data):
        w = newimg.size[0]
        (x, y) = (0, 0)

        for pixel in self.modPix(newimg.getdata(), data):

            # Putting modified pixels in the new image
            newimg.putpixel((x, y), pixel)
            if (x == w - 1):
                x = 0
                y += 1
            else:
                x += 1

    def genData(self,data):
        newd = []

        for i in data:
            newd.append(format(ord(i), '08b'))
        return newd

    def modPix(self,pix, data):
        datalist = self.genData(data)
        lendata = len(datalist)
        imdata = iter(pix)
        for i in range(lendata):
            # Extracting 3 pixels at a time
            pix = [value for value in imdata.__next__()[:3] +
                   imdata.__next__()[:3] +
                   imdata.__next__()[:3]]
            # Pixel value should be made
            # odd for 1 and even for 0
            for j in range(0, 8):
                if (datalist[i][j] == '0') and (pix[j] % 2 != 0):

                    if (pix[j] % 2 != 0):
                        pix[j] -= 1

                elif (datalist[i][j] == '1') and (pix[j] % 2 == 0):
                    pix[j] -= 1
            # Eigh^th pixel of every set tells
            # whether to stop or read further.
            # 0 means keep reading; 1 means the
            # message is over.
            if (i == lendata - 1):
                if (pix[-1] % 2 == 0):
                    pix[-1] -= 1
            else:
                if (pix[-1] % 2 != 0):
                    pix[-1] -= 1

            pix = tuple(pix)
            yield pix[0:3]
            yield pix[3:6]
            yield pix[6:9]

    def dct_encode_button_event(self):
        self.uploaded_file = tkinter.filedialog.askopenfilename(filetypes = ([('.png', '*.png'),('.jpeg', '*.jpeg'),('.jpg', '*.jpg')]))
        if not self.uploaded_file:
            messagebox.showerror("Error","You have selected nothing !")
        else:
            self.load()
            self.myimg = Image.open(self.uploaded_file)
            self.dctimg = cv2.imread(self.uploaded_file, cv2.IMREAD_UNCHANGED)
            self.myimage = self.myimg.resize((400,400))
            self.img = customtkinter.CTkImage(self.myimage, size=(400,400))
            
            self.dct_encode_frame.grid(row=1, column=0, sticky="nsew")

            self.dct_label = customtkinter.CTkLabel(self.dct_encode_frame, text="DCT Encoding", font=customtkinter.CTkFont(size=30, weight="bold"))
            self.dct_label.grid(row=0, column=0, padx=50, pady=30, columnspan=2, sticky='e')

            self.selected_image_label = customtkinter.CTkLabel(self.dct_encode_frame, text="Selected Image:", font=customtkinter.CTkFont(size=24, weight="bold"))
            self.selected_image_label.grid(row=1, column=0, padx=30, pady=0, sticky="w")
            
            self.dct_image_label = customtkinter.CTkLabel(self.dct_encode_frame, image=self.img, text="")
            self.dct_image_label.grid(row=2, column=0, padx=30, pady=15, rowspan=10)
            
            self.dct_image_name_label = customtkinter.CTkLabel(self.dct_encode_frame, text="Image Name: " + os.path.basename(self.uploaded_file))
            self.dct_image_name_label.grid(row=2, column=1, padx=30, pady=0, sticky="w")
            
            self.dct_image_size_label = customtkinter.CTkLabel(self.dct_encode_frame, text="Image Size: " + str(os.path.getsize(self.uploaded_file)) + " bytes")
            self.dct_image_size_label.grid(row=3, column=1, padx=30, pady=0, sticky="w")
            
            self.dct_image_resolution_label = customtkinter.CTkLabel(self.dct_encode_frame, text="Image Resolution: " + str(self.myimg.size[0]) + " x " + str(self.myimg.size[1]))
            self.dct_image_resolution_label.grid(row=4, column=1, padx=30, pady=0, sticky="w")
            
            self.dct_image_type_label = customtkinter.CTkLabel(self.dct_encode_frame, text="Image Type: " + self.myimg.format)
            self.dct_image_type_label.grid(row=5, column=1, padx=30, pady=0, sticky="w")
            
            self.dct_image_path_label = customtkinter.CTkLabel(self.dct_encode_frame, text="Image Path: " + self.uploaded_file)
            self.dct_image_path_label.grid(row=6, column=1, padx=30, pady=0, sticky="w", columnspan=2)
            
            self.dct_secret_message_label = customtkinter.CTkLabel(self.dct_encode_frame, text="Secret Message: ")
            self.dct_secret_message_label.grid(row=7, column=1, padx=30, pady=0, sticky="w")

            self.dct_secret_message_textbox = customtkinter.CTkTextbox(self.dct_encode_frame, width=400, height=50, font=customtkinter.CTkFont(size=12))
            self.dct_secret_message_textbox.grid(row=8, column=1, padx=30, pady=0, sticky="w", columnspan=2)
            
            self.dct_secret_message_error_label = customtkinter.CTkLabel(self.dct_encode_frame, text="")
            self.dct_secret_message_error_label.grid(row=9, column=1, padx=0, pady=0, sticky="w")

            self.dct_embed_button = customtkinter.CTkButton(self.dct_encode_frame, text="Embed", command=self.dct_embed_button_event, width=200)
            self.dct_embed_button.grid(row=10, column=1, padx=10, pady=0)
            
            self.dct_cancel_button = customtkinter.CTkButton(self.dct_encode_frame, text="Cancel", command=self.dct_encodecancel_button_event , width=200, fg_color="red", text_color="white")
            self.dct_cancel_button.grid(row=10, column=2, padx=10, pady=0)
            
            # Generate Unique ID for the watermark
            self.watermark_id = str(uuid.uuid4())
            self.watermark_data = {"owner": self.user_login['localId'] ,"name": os.path.basename(self.uploaded_file), "size": str(os.path.getsize(self.uploaded_file)), "technique": "DCT", "date": str(datetime.datetime.now())}
    
    def dct_embed_button_event(self):
        msg = self.dct_secret_message_textbox.get("1.0",END)
        self.dct_encode(self.dctimg, msg)
        
    def dct_encode(self, img, msg):
        self.message = None
        self.bitMess = None
        self.oriCol = 0
        self.oriRow = 0
        self.numBits = 0 

        secret = msg
        self.message = str(len(secret))+'*'+secret
        self.bitMess = self.toBits()
        # Get the size of image in pixels
        row,col = img.shape[:2]
        if((col/8)*(row/8)<len(secret)):
            messagebox.showerror("Error", "Message too large to encode in image")
            return False
        # Make the rows and columns divisible by 8x8
        if row%8 != 0 or col%8 != 0:
            img = self.addPadd(img, row, col)
        
        row,col = img.shape[:2]
        # Split image into its RGB channels
        bImg,gImg,rImg = cv2.split(img)
        # Message to be hid in blue channel so converted to type float32 for dct function
        bImg = np.float32(bImg)
        # Break into 8x8 blocks
        imgBlocks = [np.round(bImg[j:j+8, i:i+8]-128) for (j,i) in itertools.product(range(0,row,8),
                                                                       range(0,col,8))]
        # Blocks are run through DCT function
        dctBlocks = [np.round(cv2.dct(img_Block)) for img_Block in imgBlocks]
        # blocks then run through quantization table
        quantizedDCT = [np.round(dct_Block/quant) for dct_Block in dctBlocks]
        messIndex = 0
        letterIndex = 0
        for quantizedBlock in quantizedDCT:
            # Find LSB in DC coeff and replace with message bit
            DC = quantizedBlock[0][0]
            DC = np.uint8(DC)
            DC = np.unpackbits(DC)
            DC[7] = self.bitMess[messIndex][letterIndex]
            DC = np.packbits(DC)
            DC = np.float32(DC)
            DC= DC-255
            quantizedBlock[0][0] = DC
            letterIndex = letterIndex+1
            if letterIndex == 8:
                letterIndex = 0
                messIndex = messIndex + 1
                if messIndex == len(self.message):
                    break
        # Blocks run inversely through quantization table
        sImgBlocks = [quantizedBlock *quant+128 for quantizedBlock in quantizedDCT]
        # Blocks run through inverse DCT
        
        # Stick the new image back together
        sImg=[]
        for chunkRowBlocks in self.chunks(sImgBlocks, col/8):
            for rowBlockNum in range(8):
                for block in chunkRowBlocks:
                    sImg.extend(block[rowBlockNum])
        sImg = np.array(sImg).reshape(row, col)
        sImg = np.uint8(sImg)
        sImg = cv2.merge((sImg,gImg,rImg))
        
        # Save the image
        temp=os.path.splitext(os.path.basename(self.myimg.filename))[0]
        try:
            cv2.imwrite(tkinter.filedialog.asksaveasfilename(initialfile=temp,filetypes = ([('.png', '*.png'),('.jpeg', '*.jpeg'),('.jpg', '*.jpg')]),defaultextension=".png"),sImg)
            messagebox.showinfo("Success","Encoding Successful\nFile is encoded and saved in the selected directory")
            database.child("watermarks").child(self.watermark_id).set(self.watermark_data, self.user_login['idToken'])
            self.dct_encode_frame.grid_forget()
        except:
            messagebox.showerror("Error","File is not saved")
        
    
    def chunks(self, l, n):
        m = int(n)
        for i in range(0, len(l), m):
            yield l[i:i + m]

    def addPadd(self,img, row, col):
        img = cv2.resize(img,(col+(8-col%8),row+(8-row%8)))    
        return img
    
    def toBits(self):
        bits = []
        for char in self.message:
            binval = bin(ord(char))[2:].rjust(8,'0')
            bits.append(binval)
        self.numBits = bin(len(bits))[2:].rjust(8,'0')
        return bits
    
    # Watermark Analysis Module Methods
    def lsb_decode_button_event(self):
        self.uploaded_file = tkinter.filedialog.askopenfilename(filetypes = ([('.png', '*.png'),('.jpeg', '*.jpeg'),('.jpg', '*.jpg')]))
        if not self.uploaded_file:
            messagebox.showerror("Error","You have selected nothing !")
        else:
            self.myimg = Image.open(self.uploaded_file)
            self.myimage = self.myimg.resize((400,400))
            self.img = customtkinter.CTkImage(self.myimage, size=(400,400))

            self.hidden_data = self.decode(self.myimg)
            
            self.lsb_decode_frame = customtkinter.CTkFrame(self, bg_color="white")
            self.lsb_decode_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
            
            self.lsb_decode_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="LSB Decode", font=customtkinter.CTkFont(size=30, weight="bold"))
            self.lsb_decode_label.grid(row=0, column=0, padx=50, pady=30, sticky="nsew")
            
            self.lsb_decode_uploaded_image_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="Uploaded Image", font=customtkinter.CTkFont(size=24, weight="bold"))
            self.lsb_decode_uploaded_image_label.grid(row=1, column=0, padx=30, pady=15)
            
            self.lsb_decode_uploaded_image = customtkinter.CTkImage(Image.open(self.uploaded_file), size=(200,200))
            self.lsb_decode_uploaded_image_label = customtkinter.CTkLabel(self.lsb_decode_frame, image=self.img, text="")
            self.lsb_decode_uploaded_image_label.grid(row=2, column=0, padx=30, pady=15, rowspan=7)
            
            self.lsb_decode_uploaded_image_name_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="Image Name: " + self.uploaded_file.split("/")[-1], font=customtkinter.CTkFont(size=16, weight="bold"))
            self.lsb_decode_uploaded_image_name_label.grid(row=2, column=1, padx=30, pady=15, sticky="w")
            
            self.lsb_decode_uploaded_image_size_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="Image Size: " + str(os.path.getsize(self.uploaded_file)), font=customtkinter.CTkFont(size=16, weight="bold"))
            self.lsb_decode_uploaded_image_size_label.grid(row=3, column=1, padx=30, pady=15, sticky="w")
            
            self.lsb_decode_uploaded_image_resolution_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="Image Resolution: " + str(Image.open(self.uploaded_file).size), font=customtkinter.CTkFont(size=16, weight="bold"))
            self.lsb_decode_uploaded_image_resolution_label.grid(row=4, column=1, padx=30, pady=15, sticky="w")
            
            self.lsb_decode_uploaded_image_type_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="Image Type: " + self.uploaded_file.split(".")[-1], font=customtkinter.CTkFont(size=16, weight="bold"))
            self.lsb_decode_uploaded_image_type_label.grid(row=5, column=1, padx=30, pady=15, sticky="w")
            
            self.lsb_decode_uploaded_image_path_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="Image Path: " + self.uploaded_file, font=customtkinter.CTkFont(size=16, weight="bold"))
            self.lsb_decode_uploaded_image_path_label.grid(row=6, column=1, padx=30, pady=15, sticky="w", columnspan=2)
            
            self.lsb_decode_secret_message_label = customtkinter.CTkLabel(self.lsb_decode_frame, text="Secret Message:", font=customtkinter.CTkFont(size=16, weight="bold"))
            self.lsb_decode_secret_message_label.grid(row=7, column=1, padx=30, pady=15, sticky="w")
            
            self.lsb_decode_secret_message_textbox = customtkinter.CTkLabel(self.lsb_decode_frame, text="", width=30, height=5, font=customtkinter.CTkFont(size=16, weight="bold"), text_color="red")
            self.lsb_decode_secret_message_textbox.grid(row=8, column=1, padx=30, pady=15, sticky="w")

            self.lsb_decode_button = customtkinter.CTkButton(self.lsb_decode_frame, text="Decode", command=self.lsb_detect_button_event)
            self.lsb_decode_button.grid(row=9, column=1, padx=40, pady=0, sticky="w")

            self.lsb_decode_cancel_button = customtkinter.CTkButton(self.lsb_decode_frame, text="Cancel", fg_color="red", text_color="white", command=self.lsb_decodecancel_button_event)
            self.lsb_decode_cancel_button.grid(row=9, column=2, padx=40, pady=0, sticky="w")

    def lsb_detect_button_event(self):
        self.load()
        self.lsb_decode_secret_message_textbox.configure(text=self.hidden_data)
    
    def decode(self, myimg):
        myimg = self.myimg
        data = ''
        imgdata = iter(myimg.getdata())

        while (True):
            pixels = [value for value in imgdata.__next__()[:3] +
                      imgdata.__next__()[:3] +
                      imgdata.__next__()[:3]]
            binstr = ''
            for i in pixels[:8]:
                if i % 2 == 0:
                    binstr += '0'
                else:
                    binstr += '1'

            data += chr(int(binstr, 2))
            if pixels[-1] % 2 != 0:
                return data

    def dct_decode_button_event(self):
        self.uploaded_file = tkinter.filedialog.askopenfilename(filetypes = ([('.png', '*.png'),('.jpeg', '*.jpeg'),('.jpg', '*.jpg')]))
        if not self.uploaded_file:
            messagebox.showerror("Error","You have selected nothing !")
        else:
            self.myimg = Image.open(self.uploaded_file)
            self.myimage = self.myimg.resize((400,400))
            self.img = customtkinter.CTkImage(self.myimage, size=(400,400))
            self.dctimg = cv2.imread(self.uploaded_file, cv2.IMREAD_UNCHANGED)
            self.hidden_data = self.decode(self.myimg)
            
            self.dct_decode_frame = customtkinter.CTkFrame(self, bg_color="white")
            self.dct_decode_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
            
            self.dct_decode_label = customtkinter.CTkLabel(self.dct_decode_frame, text="DCT Decode", font=customtkinter.CTkFont(size=30, weight="bold"))
            self.dct_decode_label.grid(row=0, column=0, padx=50, pady=30, sticky="nsew")
            
            self.dct_decode_uploaded_image_label = customtkinter.CTkLabel(self.dct_decode_frame, text="Uploaded Image", font=customtkinter.CTkFont(size=24, weight="bold"))
            self.dct_decode_uploaded_image_label.grid(row=1, column=0, padx=30, pady=15)
            
            self.dct_decode_uploaded_image = customtkinter.CTkImage(Image.open(self.uploaded_file), size=(200,200))
            self.dct_decode_uploaded_image_label = customtkinter.CTkLabel(self.dct_decode_frame, image=self.img, text="")
            self.dct_decode_uploaded_image_label.grid(row=2, column=0, padx=30, pady=15, rowspan=7)
            
            self.dct_decode_uploaded_image_name_label = customtkinter.CTkLabel(self.dct_decode_frame, text="Image Name: " + self.uploaded_file.split("/")[-1], font=customtkinter.CTkFont(size=16, weight="bold"))
            self.dct_decode_uploaded_image_name_label.grid(row=2, column=1, padx=30, pady=15, sticky="w")
            
            self.dct_decode_uploaded_image_size_label = customtkinter.CTkLabel(self.dct_decode_frame, text="Image Size: " + str(os.path.getsize(self.uploaded_file)), font=customtkinter.CTkFont(size=16, weight="bold"))
            self.dct_decode_uploaded_image_size_label.grid(row=3, column=1, padx=30, pady=15, sticky="w")
            
            self.dct_decode_uploaded_image_resolution_label = customtkinter.CTkLabel(self.dct_decode_frame, text="Image Resolution: " + str(Image.open(self.uploaded_file).size), font=customtkinter.CTkFont(size=16, weight="bold"))
            self.dct_decode_uploaded_image_resolution_label.grid(row=4, column=1, padx=30, pady=15, sticky="w")
            
            self.dct_decode_uploaded_image_type_label = customtkinter.CTkLabel(self.dct_decode_frame, text="Image Type: " + self.uploaded_file.split(".")[-1], font=customtkinter.CTkFont(size=16, weight="bold"))
            self.dct_decode_uploaded_image_type_label.grid(row=5, column=1, padx=30, pady=15, sticky="w")
            
            self.dct_decode_uploaded_image_path_label = customtkinter.CTkLabel(self.dct_decode_frame, text="Image Path: " + self.uploaded_file, font=customtkinter.CTkFont(size=16, weight="bold"))
            self.dct_decode_uploaded_image_path_label.grid(row=6, column=1, padx=30, pady=15, sticky="w", columnspan=2)
            
            self.dct_decode_secret_message_label = customtkinter.CTkLabel(self.dct_decode_frame, text="Secret Message:", font=customtkinter.CTkFont(size=16, weight="bold"))
            self.dct_decode_secret_message_label.grid(row=7, column=1, padx=30, pady=15, sticky="w")
            
            self.dct_decode_secret_message_textbox = customtkinter.CTkLabel(self.dct_decode_frame, text="", width=30, height=5, font=customtkinter.CTkFont(size=16, weight="bold"), text_color="red")
            self.dct_decode_secret_message_textbox.grid(row=8, column=1, padx=30, pady=15, sticky="w")

            self.dct_decode_button = customtkinter.CTkButton(self.dct_decode_frame, text="Decode", command=self.dct_detect_button_event)
            self.dct_decode_button.grid(row=9, column=1, padx=40, pady=0, sticky="w")

            self.dct_decode_cancel_button = customtkinter.CTkButton(self.dct_decode_frame, text="Cancel", fg_color="red", text_color="white", command=self.dct_decodecancel_button_event)
            self.dct_decode_cancel_button.grid(row=9, column=2, padx=40, pady=0, sticky="w")
    
    def dct_detect_button_event(self):
        self.load()
        self.dct_decode_secret_message_textbox.configure(text=self.dct_decode(self.dctimg))

    def dct_decode(self,img):
        row,col = img.shape[:2]
        messSize = None
        messageBits = []
        buff = 0
        # Split image into RGB channels
        bImg,gImg,rImg = cv2.split(img)
        # Message hid in blue channel so converted to type float32 for dct function
        bImg = np.float32(bImg)
        # Break into 8x8 blocks
        imgBlocks = [bImg[j:j+8, i:i+8]-128 for (j,i) in itertools.product(range(0,row,8),
                                                                       range(0,col,8))]    
        # Blocks run through quantization table
        quantizedDCT = [img_Block/quant for img_Block in imgBlocks]
        i=0
        # Message extracted from LSB of DC coeff
        for quantizedBlock in quantizedDCT:
            DC = quantizedBlock[0][0]
            DC = np.uint8(DC)
            DC = np.unpackbits(DC)
            if DC[7] == 1:
                buff+=(0 & 1) << (7-i)
            elif DC[7] == 0:
                buff+=(1&1) << (7-i)
            i=1+i
            if i == 8:
                messageBits.append(chr(buff))
                buff = 0
                i =0
                if messageBits[-1] == '*' and messSize is None:
                    try:
                        messSize = int(''.join(messageBits[:-1]))
                    except:
                        pass
            if len(messageBits) - len(str(messSize)) - 1 == messSize:
                return ''.join(messageBits)[len(str(messSize))+1:]
        # Blocks run inversely through quantization table
        sImgBlocks = [quantizedBlock *quant+128 for quantizedBlock in quantizedDCT]
        # Blocks run through inverse DCT
        # Puts the new image back together
        sImg=[]
        for chunkRowBlocks in self.chunks(sImgBlocks, col/8):
            for rowBlockNum in range(8):
                for block in chunkRowBlocks:
                    sImg.extend(block[rowBlockNum])
        sImg = np.array(sImg).reshape(row, col)
        #converted from type float32
        sImg = np.uint8(sImg)
        sImg = cv2.merge((sImg,gImg,rImg))
        return ''

    # Watermark Management Module Methods
    def delete_record_event(self):
        self.selected_record = self.treeview_frame.item(self.treeview_frame.focus())
        if messagebox.askyesno("Delete Record", "Are you sure you want to delete this record?"):
            self.treeview_frame.delete(self.treeview_frame.focus())
            messagebox.showinfo("Success", "Record deleted successfully")
        else:
            messagebox.showinfo("Cancel", "Record deletion cancelled")

    # Main Method
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure window settings
        self.title("CovertMark")
        # Set the default resolution of the window to the selected resolution from self.resolution_ddl

        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)
        self.iconbitmap("Images/CovertMarkLogo.ico")

        # Images relative file paths
        # Backgrounds
        self.loginbg_image = customtkinter.CTkImage(Image.open("Images/LoginBG.png"), size=(880,720))
        self.forgotpwbg_image = customtkinter.CTkImage(Image.open("Images/ForgotPWBG.png"), size=(880,720))
        self.registerbg_image = customtkinter.CTkImage(Image.open("Images/RegisterBG.png"), size=(880,720))
        self.loadingbg_image = customtkinter.CTkImage(Image.open("Images/LoadingBG.png"), size=(720,720))
        self.about_image = customtkinter.CTkImage(Image.open("Images/AboutUsBG.png"), size=(300,300))
        self.faq_image = customtkinter.CTkImage(Image.open("Images/FAQBG.png"), size=(300,300))

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
        self.loginbg_image_label.grid(row=0, column=0, rowspan=11)

        self.logo_image_label = customtkinter.CTkLabel(self.login_frame, image=self.logo_image, text="")
        self.logo_image_label.grid(row=0, column=1, pady=(80,0))

        self.login_label = customtkinter.CTkLabel(self.login_frame, text="Welcome to CovertMark", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.login_label.grid(row=1, column=1, padx=30, pady=(15, 15))
        
        # Entry Fields
        self.logemail_entry = customtkinter.CTkEntry(self.login_frame, width=200, placeholder_text="Email")
        self.logemail_entry.grid(row=2, column=1, padx=30, pady=(15, 5))

        self.logpassword_entry = customtkinter.CTkEntry(self.login_frame, width=200, show="*", placeholder_text="Password")
        self.logpassword_entry.grid(row=3, column=1, padx=30, pady=5)

        # Error Label for invalid email and password
        self.invalid_login_label = customtkinter.CTkLabel(self.login_frame, text="", text_color="red")
        self.invalid_login_label.grid(row=4, column=1, padx=30)

        self.remember_checkbox = customtkinter.CTkCheckBox(self.login_frame, text="Remember Me")
        self.remember_checkbox.grid(row=5, column=1, padx=(100,0), pady=5, sticky="w")

        # Controls
        self.login_button = customtkinter.CTkButton(self.login_frame, text="Login", command=self.login_event, width=200)
        self.login_button.grid(row=6, column=1, padx=30, pady=5)

        self.reset_button = customtkinter.CTkButton(self.login_frame, text="Forgot password?", command=self.resetpass_event, width=200, fg_color="grey", text_color="white")
        self.reset_button.grid(row=7, column=1, padx=30, pady=(5, 15))

        self.signUpLabel = customtkinter.CTkLabel(self.login_frame, text='Not a member?')
        self.signUpLabel.grid(row=8, column=1, padx=30, pady=(5, 0))

        self.register_button = customtkinter.CTkButton(self.login_frame, text='Register Now', command=self.register_event, width=200)
        self.register_button.grid(row=9, column=1, padx=30, pady=(0, 15))
        
        self.appearance_mode = customtkinter.CTkOptionMenu(self.login_frame, values=["System", "Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode.grid(row=10, column=1, padx=20, pady=20, sticky="se")

        # ------------------------------- Register Frame ------------------------------- #

        self.register_frame = customtkinter.CTkFrame(self, corner_radius=0)

        self.registerbg_image_label = customtkinter.CTkLabel(self.register_frame, image=self.registerbg_image, text="")
        self.registerbg_image_label.grid(row=0, column=0, rowspan=16)

        self.register_label = customtkinter.CTkLabel(self.register_frame, text="Registration", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.register_label.grid(row=0, column=1, padx=115, pady=(50,5))

        # Entry Fields
        self.regemail_entry = customtkinter.CTkEntry(self.register_frame, width=200, placeholder_text="Email")
        self.regemail_entry.grid(row=1, column=1, padx=30)

        self.invalid_email_label = customtkinter.CTkLabel(self.register_frame, text="", text_color="red")
        self.invalid_email_label.grid(row=2, column=1, padx=30)

        self.regpassword_entry = customtkinter.CTkEntry(self.register_frame, width=200, show="*", placeholder_text="Password")
        self.regpassword_entry.grid(row=3, column=1, padx=30)

        self.invalid_password_label = customtkinter.CTkLabel(self.register_frame, text="", text_color="red")
        self.invalid_password_label.grid(row=4, column=1, padx=30)

        self.regconfirmpass_entry = customtkinter.CTkEntry(self.register_frame, width=200, show="*", placeholder_text="Confirm Password")
        self.regconfirmpass_entry.grid(row=5, column=1, padx=30)

        self.invalid_confirmpass_label = customtkinter.CTkLabel(self.register_frame, text="", text_color="red")
        self.invalid_confirmpass_label.grid(row=6, column=1, padx=30)

        # Controls
        self.hide_button = customtkinter.CTkButton(self.register_frame, text="", image=self.close_eye_image, command=self.unhide)
        self.hide_button.grid(row=7, column=1, padx=30, pady=(0, 5))

        self.toscheckbox = customtkinter.CTkCheckBox(self.register_frame, text="I Agree to CovertMark's Terms &\n Conditions and Privacy Policy")
        self.toscheckbox.grid(row=8, column=1, padx=30, pady=(0,5))

        self.tos_button = customtkinter.CTkButton(self.register_frame, text="Terms of Use", command=self.open_tos)
        self.tos_button.grid(row=9, column=1, padx=30, pady=(0,5))

        self.privacy_button = customtkinter.CTkButton(self.register_frame, text="Privacy Policy", command=self.open_privacy)
        self.privacy_button.grid(row=10, column=1, padx=30, pady=(0,5))

        self.signuperror_label = customtkinter.CTkLabel(self.register_frame, text="", text_color="red")
        self.signuperror_label.grid(row=11, column=1, padx=30)

        self.signup_button = customtkinter.CTkButton(self.register_frame, text="Sign Up", command=self.signup_event, width=200)
        self.signup_button.grid(row=12, column=1, padx=30)

        self.clear_button = customtkinter.CTkButton(self.register_frame, text="Clear All", command=self.clear_button_event, width=200, fg_color="red", text_color="white")
        self.clear_button.grid(row=13, column=1, padx=30)

        self.back_button = customtkinter.CTkButton(self.register_frame, text="Back", command=self.registerback_button_event, width=200, fg_color="grey", text_color="white")
        self.back_button.grid(row=14, column=1, padx=30)

        self.appearance_mode = customtkinter.CTkOptionMenu(self.register_frame, values=["System", "Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode.grid(row=15, column=1, padx=20, pady=(50, 20), sticky="se")

        # ------------------------------- Forgot Password Frame ------------------------------- #

        self.forgot_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.forgot_label = customtkinter.CTkLabel(self.forgot_frame, text="Forgot Password",
                                                 font=customtkinter.CTkFont(size=30, weight="bold"))
        self.forgot_label.grid(row=0, column=1, padx=80, pady=(150, 15))

        self.forgotpwbg_image_label = customtkinter.CTkLabel(self.forgot_frame, image=self.forgotpwbg_image, text="")
        self.forgotpwbg_image_label.grid(row=0, column=0, rowspan=6)

        # Entry Fields
        self.forgemail_entry = customtkinter.CTkEntry(self.forgot_frame, width=200, placeholder_text="Email")
        self.forgemail_entry.grid(row=1, column=1, padx=30, pady=(15, 0))

        # Error Label for invalid email
        self.invalid_forgotpw_label = customtkinter.CTkLabel(self.forgot_frame, text="", text_color="red")
        self.invalid_forgotpw_label.grid(row=2, column=1, padx=30)

        # Controls
        self.send_button = customtkinter.CTkButton(self.forgot_frame, text="Send Verification Code", command=self.send_button_event, width=200)
        self.send_button.grid(row=3, column=1, padx=30, pady=(15, 15))

        self.back_button = customtkinter.CTkButton(self.forgot_frame, text="Back", command=self.forgotback_button_event, width=200, fg_color="grey", text_color="white")
        self.back_button.grid(row=4, column=1, padx=30, pady=(0, 15))

        self.appearance_mode = customtkinter.CTkOptionMenu(self.forgot_frame, values=["System", "Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode.grid(row=5, column=1, padx=20, pady=(290, 20), sticky="se")

        # ------------------------------- Change Password Frame ------------------------------- #

        self.forgot_frame2 = customtkinter.CTkFrame(self, corner_radius=0)
        self.forgot_label = customtkinter.CTkLabel(self.forgot_frame2, text="Change Password",
                                                 font=customtkinter.CTkFont(size=30, weight="bold"))
        self.forgot_label.grid(row=0, column=1, padx=80, pady=(150, 15))

        self.forgotpwbg_image_label = customtkinter.CTkLabel(self.forgot_frame2, image=self.forgotpwbg_image, text="")
        self.forgotpwbg_image_label.grid(row=0, column=0, rowspan=6)

        # Entry Fields
        self.forgemail_entry = customtkinter.CTkEntry(self.forgot_frame2, width=200, placeholder_text="Email")
        self.forgemail_entry.grid(row=1, column=1, padx=30, pady=(15, 0))

        # Error Label for invalid email
        self.invalid_forgotpw_label = customtkinter.CTkLabel(self.forgot_frame2, text="", text_color="red")
        self.invalid_forgotpw_label.grid(row=2, column=1, padx=30)

        # Controls
        self.send_button = customtkinter.CTkButton(self.forgot_frame2, text="Send Verification Code", command=self.send2_button_event, width=200)
        self.send_button.grid(row=3, column=1, padx=30, pady=(15, 15))

        self.back_button = customtkinter.CTkButton(self.forgot_frame2, text="Back", command=self.changeback_button_event, width=200, fg_color="grey", text_color="white")
        self.back_button.grid(row=4, column=1, padx=30, pady=(0, 15))

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
        self.logout_button.grid(row=0, column=7, padx=11,sticky="e")

        # ------------------------------- Home Frame ------------------------------- #

        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_rowconfigure(0, weight=1)

        self.home_tabs = customtkinter.CTkTabview(self.home_frame, width= 1000, height=600)
        self.home_tabs.grid(row=1, column=0, padx=120, pady=20, sticky="nsew")

        #add content to the tabs
        self.home_tabs.add("About").grid_columnconfigure(0, weight=1)
        self.home_tabs.add("FAQ").grid_columnconfigure(0, weight=1)

        self.about_tab = customtkinter.CTkLabel(self.home_tabs.tab("About"), text="About CovertMark", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.about_tab.grid(row=0, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)

        self.about_image_label = customtkinter.CTkLabel(self.home_tabs.tab("About"), image=self.about_image, text="")
        self.about_image_label.grid(row=1, column=0, padx=20, pady=20, sticky="nsew", rowspan=2)

        self.about_info = customtkinter.CTkLabel(self.home_tabs.tab("About"), text="CovertMark is a digital watermarking application for a final year project by Khoo Ed Win\nstudying Bachelor of Software Engineering(Honours) at Tunku Abdul Rahman University\nof Management and Technology (TARUMT)\n\nThis project's mission is to empower content creators, businesses, and individuals with\ninnovative and user-friendly solutions that safeguard their valuable digital assets against\npiracy and unauthorized distribution. I strive to provide cutting-edge technologies that\nenhance the integrity and ownership of digital media.\n\nIn an age where digital content is easily shared and accessed, ensuring the rightful ownership\nand protection of intellectual property has never been more crucial. Our vision is to\nestablish CovertMark as the go-to solution for seamlessly embedding robust watermarks\nusing advanced steganography techniques. By offering an intuitive and comprehensive platform,\nwe aim to minimize the risks associated with digital piracy, content misuse, and data breaches.")
        self.about_info.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

        self.faq_tab = customtkinter.CTkLabel(self.home_tabs.tab("FAQ"), text="Frequently Asked Questions", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.faq_tab.grid(row=0, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)

        self.faq_image_label = customtkinter.CTkLabel(self.home_tabs.tab("FAQ"), image=self.faq_image, text="")
        self.faq_image_label.grid(row=1, column=2, padx=20, pady=20, sticky="nsew")

        self.faq_info = customtkinter.CTkLabel(self.home_tabs.tab("FAQ"), text="1. What is CovertMark?\nCovertMark is an advanced digital watermarking application that uses steganography\ntechniques to invisibly embed watermarks in your digital media, protecting your content\nfrom unauthorised use and distribution.\n\n2. How does CovertMark work?\nCovertMark employs cutting-edge steganography algorithms like Discrete Cosine\n Transform and Least Significant Bit to embed watermarks into your images\nwithout altering their appearance.\n\n3. Why do I need CovertMark?\nIn today's digital age, content piracy and misuse are rampant. CovertMark empowers you to\nsecure your digital creations by adding invisible watermarks that deter theft and help you\nmaintain control over your intellectual property.\n\n4. What support options are available?\nCurrently, Covertmark only supports image files and are looking into upgrading\nto support more media file types\n\n5. Can I upload my watermarks to CovertMark?\nCurrently, you cannot upload your own watermarks to CovertMark for safe storage yet.")
        self.faq_info.grid(row=1, column=0, padx=20, pady=20, sticky="w")


        # ------------------------------- Watermark Encoding Frame ------------------------------- #
        # Left side
        self.encoding_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.encoding_label = customtkinter.CTkLabel(self.encoding_frame,   text=" Watermark Encoding ", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.encoding_label.grid(row=0, column=0, padx=500, pady=20, sticky="nsew", columnspan=2)

        self.empty1_label = customtkinter.CTkLabel(self.encoding_frame, text="")
        self.empty1_label.grid(row=1, column=0, padx=20, pady=40, sticky="nsew", columnspan=2)

        self.stegano_label = customtkinter.CTkLabel(self.encoding_frame, text="Choose a steganography technique", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.stegano_label.grid(row=2, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)

        self.lsb_encode_button = customtkinter.CTkButton(self.encoding_frame, text="Least Significant\nBit (LSB)", width=150, height=150, command=self.lsb_encode_button_event, font=customtkinter.CTkFont(size=44, weight="bold"))
        self.lsb_encode_button.grid(row=3, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)


        self.dct_encode_button = customtkinter.CTkButton(self.encoding_frame, text="Discrete Cosine\nTransform (DCT)", width=150, height=150, command=self.dct_encode_button_event, font=customtkinter.CTkFont(size=44, weight="bold"))
        self.dct_encode_button.grid(row=4, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)

        self.empty4_label = customtkinter.CTkLabel(self.encoding_frame, text="")
        self.empty4_label.grid(row=5, column=0, padx=20, pady=40, sticky="nsew", columnspan=2)

        self.lsb_encode_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.dct_encode_frame = customtkinter.CTkFrame(self, corner_radius=0)

        # ------------------------------- Watermark Decoding Module Frame ------------------------------- #

        self.decoding_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.decoding_label = customtkinter.CTkLabel(self.decoding_frame, text=" Watermark Decoding", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.decoding_label.grid(row=0, column=0, padx=500, pady=20, sticky="nsew", columnspan=2)

        self.empty5_label = customtkinter.CTkLabel(self.decoding_frame, text="")
        self.empty5_label.grid(row=1, column=0, padx=20, pady=40, sticky="nsew", columnspan=2)

        self.stegano_label = customtkinter.CTkLabel(self.decoding_frame, text="Choose a steganography technique", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.stegano_label.grid(row=2, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)

        self.lsb_decode_button = customtkinter.CTkButton(self.decoding_frame, text="Least Significant\nBit (LSB)", width=150, height=150, command=self.lsb_decode_button_event, font=customtkinter.CTkFont(size=44, weight="bold"))
        self.lsb_decode_button.grid(row=3, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)

        self.dct_decode_button = customtkinter.CTkButton(self.decoding_frame, text="Discrete Cosine\nTransform (DCT)", width=150, height=150, command=self.dct_decode_button_event, font=customtkinter.CTkFont(size=44, weight="bold"))
        self.dct_decode_button.grid(row=4, column=0, padx=20, pady=20, sticky="nsew", columnspan=2)

        self.empty6_label = customtkinter.CTkLabel(self.decoding_frame, text="")
        self.empty6_label.grid(row=5, column=0, padx=20, pady=40, sticky="nsew", columnspan=2)

        self.lsb_decode_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.dct_decode_frame = customtkinter.CTkFrame(self, corner_radius=0)

        # ------------------------------- Watermark Management Module Frame ------------------------------- #
        self.management_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.management_label = customtkinter.CTkLabel(self.management_frame, text="Watermarks History", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.management_label.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        #create a treeview with a scrollbar
        style = ttk.Style()
        style.configure("Treeview", font=customtkinter.CTkFont(size=12), rowheight=50) #modify the font of the body
        style.configure("Treeview.Heading", font=customtkinter.CTkFont(size=16, weight="bold"), rowheight=50)
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) #remove the borders

        self.scrollbar = ttk.Scrollbar(self.management_frame, orient="vertical")
        self.scrollbar.grid(row=1, column=1, sticky="ns", rowspan=9)
        # Fetch watermarks from database according to the user id
        self.treeview_frame = ttk.Treeview(self.management_frame, show="headings", yscrollcommand=self.scrollbar.set, height=10)
        self.treeview_frame["columns"] = ("Name", "Technique", "Size (bytes)", "Date Created")
        for column in self.treeview_frame["columns"]:
            self.treeview_frame.column(column, width=250, anchor="center", minwidth=250, stretch=False)
            self.treeview_frame.heading(column, text=column)
        
        self.treeview_frame.grid(row=1, column=0, padx=(20,0), pady=10, sticky="nsew", rowspan = 9)
        self.scrollbar.config(command=self.treeview_frame.yview)

        self.selected_record_label = customtkinter.CTkLabel(self.management_frame, text="Selected Record", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.selected_record_label.grid(row=1, column=2, padx=40, pady=10, sticky="nsew")

        self.delete_record_button = customtkinter.CTkButton(self.management_frame, text="Delete", fg_color="red", text_color="white", width=40, height = 10, command=self.delete_record_event)
        self.delete_record_button.grid(row=2, column=2, padx=40, pady=30, sticky="nsew")

        # ------------------------------- Loading Screen ------------------------------- #
        self.loading_frame = customtkinter.CTkFrame(self, corner_radius=0)
        # insert image here
        self.loadingbg_image_label = customtkinter.CTkLabel(self.loading_frame, image=self.loadingbg_image, text="")
        self.loadingbg_image_label.grid(row=0, column=0, padx=280)

        # ------------------------------- Profile Frame ------------------------------- #
        self.profile_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.profile_label = customtkinter.CTkLabel(self.profile_frame, text="Your Profile", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.profile_label.grid(row=0, column=0, padx=550, pady=10, columnspan=4)
        
        #create empty label
        self.empty2_label = customtkinter.CTkLabel(self.profile_frame, text="")
        self.empty2_label.grid(row=1, column=0, padx=20, pady=60, sticky="nsew", columnspan=2)

        # Label for user's name
        self.name_label = customtkinter.CTkLabel(self.profile_frame, text="Name :")
        self.name_label.grid(row=2, column=0, padx=(400,20), pady=10, sticky="e")
        self.name_entry = customtkinter.CTkEntry(self.profile_frame, width=200, placeholder_text="Name")
        self.name_entry.grid(row=2, column=1, padx=(20,200), pady=10, sticky="w")

        # Label for user's email
        self.profile_email_label = customtkinter.CTkLabel(self.profile_frame, text="Email :")
        self.profile_email_label.grid(row=3, column=0, padx=(400,20), pady=10, sticky="e")

        self.profile_email_entry = customtkinter.CTkEntry(self.profile_frame, width=200, placeholder_text="Email")
        self.profile_email_entry.grid(row=3, column=1, padx=(20,200), pady=10, sticky="w")

        # Label and button to change password
        self.changepw_label = customtkinter.CTkLabel(self.profile_frame, text="Password :")
        self.changepw_label.grid(row=4, column=0, padx=(400,20), pady=10, sticky="e")
        self.changepw_button = customtkinter.CTkButton(self.profile_frame, text="Change Password", command=self.sendchangepw_event)
        self.changepw_button.grid(row=4, column=1, padx=(20,200), pady=10, sticky="w")

        # Label for user's organisation/company
        self.org_label = customtkinter.CTkLabel(self.profile_frame, text="Organisation/Company :")
        self.org_label.grid(row=5, column=0, padx=(400,20), pady=10, sticky="e")
        self.org_entry = customtkinter.CTkEntry(self.profile_frame, width=200, placeholder_text="Organisation/Company")
        self.org_entry.grid(row=5, column=1, padx=(20,200), pady=10, sticky="w")

        # Button to save changes
        self.save_button = customtkinter.CTkButton(self.profile_frame, text="Save Changes", command=self.save_changes_event)
        self.save_button.grid(row=6, column=0, padx=(400,20), pady=10, sticky="e")

        # Button to cancel changes
        self.cancel_button = customtkinter.CTkButton(self.profile_frame, text="Cancel", fg_color="grey", text_color="white", command=self.cancel_changes_event)
        self.cancel_button.grid(row=6, column=1, padx=(20,200), pady=10, sticky="w")

        self.empty3_label = customtkinter.CTkLabel(self.profile_frame, text="")
        self.empty3_label.grid(row=7, column=0, padx=20, pady=40, sticky="nsew", columnspan=2)

        # Button to delete account
        self.delete_button = customtkinter.CTkButton(self.profile_frame, text="Delete Account", fg_color="red", text_color="white", width=20, command=self.delete_account_event)
        self.delete_button.grid(row=8, column=0, padx=550, pady=50, columnspan=4)

    
        # ------------------------------- Settings Frame ------------------------------- #
        self.settings_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.settings_label = customtkinter.CTkLabel(self.settings_frame, text="Settings", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.settings_label.grid(row=0, column=0, padx=575, pady=10, columnspan=2)
        
        self.resolution_label = customtkinter.CTkLabel(self.settings_frame, text="Resolution")
        self.resolution_label.grid(row=1, column=0, padx=50, pady=40, sticky="nsew")
        self.resolution_list = ["1920x1080", "1600x900", "1280x720"]
        self.resolution_ddl = customtkinter.CTkComboBox(self.settings_frame, values=self.resolution_list, command=self.change_resolution_event)
        self.resolution_ddl.grid(row=1, column=1, padx=50, pady=40, sticky="nsew")

        self.display_label = customtkinter.CTkLabel(self.settings_frame, text="Display")
        self.display_label.grid(row=2, column=0, padx=50, pady=40, sticky="nsew")
        self.display_list = ["Windowed", "Fullscreen"]
        self.display_ddl = customtkinter.CTkComboBox(self.settings_frame, values=self.display_list, command=self.change_display_event)
        self.display_ddl.grid(row=2, column=1, padx=50, pady=40, sticky="nsew")
      
        # create a disclaimer textbox
        self.disclaimer_text = customtkinter.CTkTextbox(self.settings_frame, width=350, height=300, border_width=1, border_color="black", corner_radius=0)
        self.disclaimer_text.grid(row=3, column=0, padx=50, pady=50, sticky="nsew", columnspan=2)
        self.disclaimer_text.insert("0.0", "Disclaimer\n\nThe CovertMark Digital Steganography Watermark Application is developed solely for educational and research purposes. The application is not intended for any illegal, unethical, or unauthorized use, including copyright infringement or data manipulation.\n\nThe creators of the CovertMark Digital Steganography Watermark Application do not assume any liability for the misuse of the application or any content that may be generated using the application. Users are solely responsible for complying with all applicable laws and regulations related to the use of the application.\n\nWhile every effort has been made to ensure the accuracy and reliability of the application, the creators make no representations or warranties regarding the functionality, accuracy, or performance of the application. Users are advised to use the application at their own risk.\n\nThe creators of the CovertMark Digital Steganography Watermark Application shall not be liable for any damages, including but not limited to direct, indirect, incidental, or consequential damages, arising from the use or inability to use the application.\n\nBy using the CovertMark Digital Steganography Watermark Application, you agree to the terms and conditions outlined in the Terms and Conditions document. If you do not agree with any part of these terms, please refrain from using the application.\n\nThe CovertMark Digital Steganography Watermark Application is a research project and should be treated as such. The creators reserve the right to update or modify the application, and to discontinue support for older versions of the application.\n\nAny information or content generated by the application is for informational purposes only and should not be considered as professional advice.\n\nBy using the CovertMark Digital Steganography Watermark Application, you acknowledge that you have read, understood, and agreed to this disclaimer.")


        # Default Settings
        self.navigate("Home")
        self.is_fullscreen = False
        self.previous_resolution = None
        self.resolution_ddl.set("1280x720")

if __name__ == "__main__":
    app = App()
    app.mainloop()