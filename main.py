
from flask import Flask, render_template, request, jsonify
import smtplib
import email.mime.text
import email.mime.multipart
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import threading
import time
import os
import random
import json
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Global variables
email_logs = []
gmail_accounts = []
whatsapp_number = ""
scheduler = None
campaign_active = False

# Configuration file path
CONFIG_FILE = 'user_config.json'
DB_FILE = 'email_logs.db'

# Long professional email templates
EMAIL_TEMPLATES = [
    {
        "subject": "Request to Review WhatsApp Ban – {{phone_number}}",
        "body": """Dear WhatsApp Support Team,

I am writing to respectfully request a review of the recent ban placed on my WhatsApp account associated with {{phone_number}}. I understand that WhatsApp has strict policies, and I sincerely apologize if my account violated any terms.

If this was an automated ban or a misunderstanding, I kindly urge your team to take a closer look. I value the platform and will ensure strict compliance in the future.

I have been a loyal user of WhatsApp for years and rely on it for important personal and professional communications. This sudden ban has significantly impacted my daily life.

I promise to adhere to all community guidelines and terms of service going forward. Please consider giving me another chance to be a responsible member of the WhatsApp community.

Thank you for your time and consideration.

Sincerely,
{{phone_number}}"""
    },
    {
        "subject": "Appeal for WhatsApp Account Restoration – {{phone_number}}",
        "body": """Dear WhatsApp Support,

My WhatsApp account {{phone_number}} has been permanently banned, and I would like to formally request a review of this decision. I believe there may have been a misunderstanding or technical error.

I have always used WhatsApp responsibly and have never intentionally violated any community guidelines. This platform is essential for my communication with family, friends, and colleagues.

I understand the importance of maintaining a safe environment on WhatsApp and fully support your efforts to do so. However, I believe my account was flagged incorrectly.

I would be extremely grateful if you could manually review my case and consider reinstating my account. I am committed to following all rules and regulations strictly.

I await your positive response and thank you for your understanding.

Respectfully,
{{phone_number}}"""
    },
    {
        "subject": "WhatsApp Account Ban Review Request – {{phone_number}}",
        "body": """Hello WhatsApp Support Team,

I am reaching out regarding the ban placed on my account {{phone_number}}. I would like to request a thorough review of this decision as I believe it may have been issued in error.

My WhatsApp account is crucial for staying connected with my family members who live abroad. The sudden ban has created significant communication barriers for me.

I have carefully reviewed your terms of service and community guidelines, and I cannot identify any actions I may have taken that would warrant this ban. I have always been a respectful user.

I kindly request that a human representative review my account activity and consider lifting this ban. I am willing to provide any additional information you may need.

Thank you for your time and for providing such an important communication platform. I hope we can resolve this matter quickly.

Kind regards,
{{phone_number}}"""
    },
    {
        "subject": "Request to Reinstate WhatsApp Account – {{phone_number}}",
        "body": """Dear WhatsApp Team,

I am writing to request the reinstatement of my WhatsApp account {{phone_number}}, which was recently banned. I believe this action may have been taken due to a technical error or misunderstanding.

WhatsApp is an integral part of my daily communication, and I have always followed your community guidelines diligently. I am committed to maintaining the highest standards of conduct on your platform.

The ban has caused considerable inconvenience as I rely on WhatsApp for coordinating with my work team and staying in touch with elderly family members who are not tech-savvy enough to use alternative platforms.

I would be deeply grateful if you could review my case manually and consider restoring my account access. I promise to continue being a responsible and respectful user of your service.

Please let me know if you need any additional information from my side to process this appeal.

Thank you for your consideration,
{{phone_number}}"""
    },
    {
        "subject": "WhatsApp Account Ban Appeal – {{phone_number}}",
        "body": """Dear Support Team,

I hope this message finds you well. I am writing to appeal the permanent ban on my WhatsApp account {{phone_number}} which came as a complete surprise to me.

I am confident that this ban was applied in error, as I have always been mindful of WhatsApp's terms and conditions. I have never sent spam messages, shared inappropriate content, or engaged in any prohibited activities.

WhatsApp serves as my primary communication tool for both personal and professional purposes. The ban has severely disrupted my ability to communicate with clients, colleagues, and loved ones.

I would like to request a manual review of my account by your team. I am certain that upon closer inspection, you will find that the ban was issued incorrectly.

I value WhatsApp as a communication platform and promise to adhere to all terms and conditions with even greater care in the future.

Respectfully yours,
{{phone_number}}"""
    },
    {
        "subject": "Urgent: WhatsApp Account Unban Request – {{phone_number}}",
        "body": """Dear WhatsApp Support,

I am contacting you regarding the unexpected ban on my WhatsApp account {{phone_number}}. This has caused significant inconvenience in my daily communication and professional activities.

I have been using WhatsApp for several years without any issues and have always respected the platform's guidelines. I am genuinely puzzled by this ban and believe it may be the result of an automated error.

The timing of this ban is particularly challenging as I am currently coordinating important family matters and work projects through WhatsApp. Many of my contacts rely solely on this platform for communication.

I would be extremely grateful if you could prioritize a manual review of my account. I am confident that you will find no legitimate reason for this ban upon closer examination.

I appreciate your prompt attention to this matter and look forward to having my account restored soon.

Best wishes,
{{phone_number}}"""
    },
    {
        "subject": "WhatsApp Account Recovery Request – {{phone_number}}",
        "body": """Hello,

I am writing to formally request the recovery of my banned WhatsApp account {{phone_number}}. I believe this ban was issued incorrectly and would like to appeal this decision.

I have reviewed WhatsApp's terms of service thoroughly and cannot identify any actions on my part that would justify this ban. I have always used the platform for legitimate communication purposes only.

As a small business owner, WhatsApp is essential for communicating with my customers and suppliers. This ban has significantly impacted my business operations and customer relationships.

I understand that WhatsApp must maintain strict standards to ensure user safety, and I fully support these efforts. However, I believe my account was caught in an incorrect automated action.

I would be most grateful if you could investigate this matter and restore my access. I am ready to provide any additional verification or information you may require.

Thank you for your consideration,
{{phone_number}}"""
    },
    {
        "subject": "Appeal for Account Reinstatement – {{phone_number}}",
        "body": """Dear WhatsApp Customer Service,

I am reaching out to appeal the ban on my WhatsApp account {{phone_number}}. I was surprised to discover that my account had been permanently banned without any prior warning or explanation.

I have always used WhatsApp responsibly and in compliance with your guidelines. My account primarily consists of family group chats, work communications, and conversations with close friends.

This ban has created significant challenges for me as WhatsApp is my primary means of communication with family members in different countries. Many important conversations and shared memories are stored in this account.

I believe this ban may be the result of an automated system error or a false report. I would appreciate if a human reviewer could examine my account activity and reconsider this decision.

I am committed to continuing as a responsible user and would be grateful for the opportunity to regain access to my account.

With gratitude,
{{phone_number}}"""
    },
    {
        "subject": "Request for Manual Review – WhatsApp Account {{phone_number}}",
        "body": """Dear WhatsApp Support Team,

I am writing to request a manual review of the ban placed on my account {{phone_number}}. I believe there has been an error in the automated system that led to this incorrect ban.

Throughout my years of using WhatsApp, I have always been a responsible user of your platform. I have never engaged in spamming, harassment, or any other prohibited activities.

This account contains years of important conversations with family, friends, and colleagues. The sudden loss of access has been emotionally and practically challenging for me.

I understand that maintaining platform safety requires strict measures, and I fully support WhatsApp's efforts in this regard. However, I am confident that my account was flagged incorrectly.

I kindly ask for your help in reviewing and reversing this decision. I am prepared to provide any additional information or verification that may be required.

Thank you for your time and understanding,
{{phone_number}}"""
    },
    {
        "subject": "WhatsApp Account Ban Dispute – {{phone_number}}",
        "body": """Dear Team,

I would like to dispute the ban on my WhatsApp account {{phone_number}}. I believe this action was taken without proper justification and would like to request a comprehensive review.

I have carefully examined my usage patterns and cannot identify any behavior that would violate WhatsApp's terms of service. I have always been mindful of community guidelines and have used the platform solely for legitimate purposes.

The ban has disrupted my ability to communicate with my elderly parents who rely on WhatsApp voice calls due to poor traditional phone connectivity in their area. This has caused considerable distress for our family.

I respectfully request that you reconsider this decision and restore my account access. I am willing to accept any reasonable conditions you may impose to ensure continued compliance.

I trust in WhatsApp's commitment to fair treatment of users and hope for a positive resolution to this matter.

Sincerely,
{{phone_number}}"""
    },
    {
        "subject": "Formal Appeal for WhatsApp Account {{phone_number}}",
        "body": """Dear WhatsApp Support,

I am submitting a formal appeal regarding the ban on my WhatsApp account {{phone_number}}. I believe this decision was made in error and would like to request a thorough reconsideration.

I have been a loyal user of WhatsApp for many years and have always respected the platform's rules and regulations. My usage has been consistent with normal personal and professional communication patterns.

The account in question is vital for my role as a community volunteer, where I coordinate with team members and communicate with beneficiaries of our programs. The ban has hindered these important social activities.

I am confident that a detailed review of my account activity will demonstrate that I have not violated any policies. I would greatly appreciate if an experienced team member could manually examine my case.

I remain committed to being a positive member of the WhatsApp community and hope for a swift resolution to this misunderstanding.

Thank you for your attention,
{{phone_number}}"""
    },
    {
        "subject": "WhatsApp Account Restoration Appeal – {{phone_number}}",
        "body": """Hello WhatsApp Support,

I am writing to appeal for the restoration of my WhatsApp account {{phone_number}}, which has been banned. I am committed to following all WhatsApp policies and believe this ban may have been issued mistakenly.

My WhatsApp account serves as the primary communication channel for my work as a freelance consultant. Many of my clients prefer WhatsApp for project discussions and file sharing, making this ban particularly problematic for my livelihood.

I have always maintained professional and respectful communication on the platform. I have never sent unsolicited messages, shared inappropriate content, or engaged in any activities that could be considered spam.

I would be very grateful if you could review my case with fresh eyes and consider reinstating my account. I understand the importance of platform integrity and promise to continue following all guidelines meticulously.

Your assistance in resolving this matter would be deeply appreciated and would allow me to resume my professional activities without further disruption.

Best regards,
{{phone_number}}"""
    },
    {
        "subject": "Request for Account Reactivation – {{phone_number}}",
        "body": """Dear WhatsApp Team,

I hope you are doing well. I am writing to request the reactivation of my banned WhatsApp account {{phone_number}}. I believe this ban was applied incorrectly and would like to appeal this decision.

I have always used WhatsApp for legitimate communication purposes and have not engaged in any prohibited activities. My account primarily consists of conversations with family, friends, and colleagues in a professional context.

As someone who travels frequently for work, WhatsApp has been my most reliable means of staying connected with my support network. The ban has created significant communication challenges during my current business trip.

I have reviewed your community guidelines once again and remain confident that my usage has been fully compliant. I would appreciate if you could investigate this matter and restore my access.

I am committed to maintaining the highest standards of conduct on your platform and would be grateful for the opportunity to continue as a responsible user.

Thank you for your time and consideration,
{{phone_number}}"""
    },
    {
        "subject": "WhatsApp Account Ban Review – {{phone_number}}",
        "body": """Dear Support Staff,

I am contacting you to request a review of the ban imposed on my WhatsApp account {{phone_number}}. I believe this decision was made in error, as I have always been a compliant and respectful user of your service.

My WhatsApp account is essential for maintaining contact with my extended family spread across different continents. We use it for sharing important family updates, coordinating events, and staying emotionally connected despite physical distances.

I have never violated any of WhatsApp's policies and have always used the platform in accordance with its intended purpose. I am genuinely confused about the reason for this ban and believe it may be a technical error.

I would be honored if you could take another look at my case and consider lifting this ban. I am prepared to provide any additional information or clarification that might be helpful for your review process.

Your help in resolving this situation would mean a great deal to me and my family who are also affected by this communication disruption.

With appreciation,
{{phone_number}}"""
    },
    {
        "subject": "Emergency Appeal: WhatsApp Account {{phone_number}}",
        "body": """Dear WhatsApp Customer Support,

I am writing this emergency appeal regarding my banned WhatsApp account {{phone_number}}. This account is essential for my daily communication, and I believe the ban was applied incorrectly.

As a healthcare worker, I rely on WhatsApp to coordinate with my team during emergencies and to communicate with patients' families during critical situations. The ban has severely impacted my ability to perform these vital functions.

I have always maintained the highest level of professionalism in my WhatsApp communications and have never shared sensitive information inappropriately or violated any platform policies.

I urgently request your review and assistance in restoring my account access. The nature of my work requires immediate and reliable communication capabilities, which this ban has completely disrupted.

I understand that WhatsApp receives many appeals, but I hope you can prioritize this case given the essential nature of my work and the impact on patient care coordination.

I thank you in advance for your help and understanding in this critical matter.

Respectfully,
{{phone_number}}"""
    }
]

# WhatsApp support email addresses
WHATSAPP_EMAILS = [
    "support@support.whatsapp.com",
    "iphone@support.whatsapp.com", 
    "android@support.whatsapp.com",
    "grievance_officer_wa@support.whatsapp.com",
    "smb@support.whatsapp.com",
    "smb.web@support.whatsapp.com",
    "accesbility@support.whatsapp.com"
]

def init_database():
    """Initialize SQLite database for logs"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            gmail_id TEXT,
            status TEXT,
            details TEXT,
            template_used TEXT,
            recipients TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_config(data):
    """Save user configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def load_config():
    """Load user configuration from JSON file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def log_email(gmail_id, status, details="", template_used=""):
    """Add email log entry to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'gmail_id': gmail_id,
            'status': status,
            'details': details,
            'template_used': template_used,
            'recipients': ', '.join(WHATSAPP_EMAILS)
        }
        
        cursor.execute('''
            INSERT INTO email_logs (timestamp, gmail_id, status, details, template_used, recipients)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (log_entry['timestamp'], log_entry['gmail_id'], log_entry['status'], 
              log_entry['details'], log_entry['template_used'], log_entry['recipients']))
        
        conn.commit()
        conn.close()
        
        # Also keep in memory for immediate access
        email_logs.append(log_entry)
        if len(email_logs) > 100:
            email_logs.pop(0)
    except Exception as e:
        print(f"Error logging email: {e}")

def load_logs_from_db():
    """Load recent logs from database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, gmail_id, status, details, template_used, recipients
            FROM email_logs
            ORDER BY id DESC
            LIMIT 100
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        global email_logs
        email_logs = []
        for row in rows:
            email_logs.append({
                'timestamp': row[0],
                'gmail_id': row[1],
                'status': row[2],
                'details': row[3],
                'template_used': row[4],
                'recipients': row[5]
            })
    except Exception as e:
        print(f"Error loading logs from database: {e}")

def send_email_batch(gmail_id, app_password, phone_number):
    """Send emails to all WhatsApp support addresses"""
    try:
        # Create SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_id, app_password)
        
        emails_sent = 0
        templates_used = []
        
        # Send 10 emails (repeat some addresses to reach 10)
        for i in range(10):
            recipient = WHATSAPP_EMAILS[i % len(WHATSAPP_EMAILS)]
            
            # Select a random template
            template = random.choice(EMAIL_TEMPLATES)
            subject = template['subject'].replace('{{phone_number}}', phone_number)
            body = template['body'].replace('{{phone_number}}', phone_number)
            
            templates_used.append(f"Template {EMAIL_TEMPLATES.index(template) + 1}")
            
            msg = email.mime.multipart.MIMEMultipart()
            msg['From'] = gmail_id
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(email.mime.text.MIMEText(body, 'plain'))
            
            server.send_message(msg)
            emails_sent += 1
            time.sleep(1)  # Small delay between emails
        
        server.quit()
        log_email(gmail_id, f"SUCCESS - {emails_sent} emails sent", 
                 template_used=f"Used templates: {', '.join(set(templates_used))}")
        return True
        
    except Exception as e:
        log_email(gmail_id, f"FAILED - {str(e)}")
        return False

def scheduled_email_job():
    """Job function for scheduled email sending"""
    if not campaign_active:
        return
        
    for account in gmail_accounts:
        try:
            send_email_batch(
                account['gmail_id'],
                account['app_password'], 
                whatsapp_number
            )
        except Exception as e:
            log_email(account['gmail_id'], f"ERROR - {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_config')
def get_config():
    """Get saved configuration"""
    config = load_config()
    return jsonify({'config': config})

@app.route('/save_config', methods=['POST'])
def save_config_route():
    """Save user configuration"""
    try:
        data = request.json
        if save_config(data):
            return jsonify({'success': True, 'message': 'Configuration saved successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving configuration: {str(e)}'})

@app.route('/start_campaign', methods=['POST'])
def start_campaign():
    global gmail_accounts, whatsapp_number, scheduler, campaign_active
    
    try:
        data = request.json
        
        # Validate input
        if not data.get('whatsapp_number'):
            return jsonify({'success': False, 'message': 'WhatsApp number is required'})
        
        # Collect Gmail accounts
        gmail_accounts = []
        for i in range(1, 5):
            gmail_id = data.get(f'gmail_id_{i}')
            app_password = data.get(f'app_password_{i}')
            
            if gmail_id and app_password:
                gmail_accounts.append({
                    'gmail_id': gmail_id,
                    'app_password': app_password
                })
        
        if not gmail_accounts:
            return jsonify({'success': False, 'message': 'At least one Gmail account is required'})
        
        whatsapp_number = data['whatsapp_number']
        
        # Save configuration
        save_config(data)
        
        # Stop existing scheduler if running
        if scheduler and scheduler.running:
            scheduler.shutdown()
        
        # Create new scheduler
        scheduler = BackgroundScheduler()
        
        # Schedule jobs for 6 AM, 12 PM, and 6 PM
        scheduler.add_job(
            func=scheduled_email_job,
            trigger="cron",
            hour=6,
            minute=0,
            id='morning_job'
        )
        
        scheduler.add_job(
            func=scheduled_email_job,
            trigger="cron", 
            hour=12,
            minute=0,
            id='noon_job'
        )
        
        scheduler.add_job(
            func=scheduled_email_job,
            trigger="cron",
            hour=18,
            minute=0,
            id='evening_job'
        )
        
        scheduler.start()
        campaign_active = True
        
        log_email("SYSTEM", f"Campaign started with {len(gmail_accounts)} Gmail accounts")
        
        return jsonify({
            'success': True, 
            'message': f'Campaign started successfully with {len(gmail_accounts)} Gmail accounts!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting campaign: {str(e)}'})

@app.route('/stop_campaign', methods=['POST'])
def stop_campaign():
    global scheduler, campaign_active
    
    try:
        if scheduler and scheduler.running:
            scheduler.shutdown()
        campaign_active = False
        log_email("SYSTEM", "Campaign stopped")
        return jsonify({'success': True, 'message': 'Campaign stopped successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping campaign: {str(e)}'})

@app.route('/get_logs')
def get_logs():
    return jsonify({'logs': email_logs})

@app.route('/test_email', methods=['POST'])
def test_email():
    """Send test emails from all 4 Gmail accounts (40 total emails)"""
    try:
        data = request.json
        phone_number = data.get('whatsapp_number')
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'WhatsApp number is required for test'})
        
        # Get all Gmail accounts from saved config or current input
        test_accounts = []
        for i in range(1, 5):
            gmail_id = data.get(f'gmail_id_{i}')
            app_password = data.get(f'app_password_{i}')
            
            if gmail_id and app_password:
                test_accounts.append({
                    'gmail_id': gmail_id,
                    'app_password': app_password
                })
        
        if not test_accounts:
            return jsonify({'success': False, 'message': 'At least one Gmail account is required for testing'})
        
        total_sent = 0
        failed_accounts = []
        
        # Send from each Gmail account
        for account in test_accounts:
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(account['gmail_id'], account['app_password'])
                
                emails_sent = 0
                templates_used = []
                
                # Send 10 emails from this account (to all 7 WhatsApp emails, some repeated)
                for i in range(10):
                    recipient = WHATSAPP_EMAILS[i % len(WHATSAPP_EMAILS)]
                    
                    # Select a random template
                    template = random.choice(EMAIL_TEMPLATES)
                    subject = template['subject'].replace('{{phone_number}}', phone_number)
                    body = template['body'].replace('{{phone_number}}', phone_number)
                    
                    template_num = EMAIL_TEMPLATES.index(template) + 1
                    templates_used.append(f"Template {template_num}")
                    
                    msg = email.mime.multipart.MIMEMultipart()
                    msg['From'] = account['gmail_id']
                    msg['To'] = recipient
                    msg['Subject'] = subject
                    msg.attach(email.mime.text.MIMEText(body, 'plain'))
                    
                    server.send_message(msg)
                    emails_sent += 1
                    time.sleep(0.5)  # Small delay between emails
                
                server.quit()
                total_sent += emails_sent
                
                log_email(account['gmail_id'], f"TEST SUCCESS - {emails_sent} emails sent", 
                         template_used=f"Used templates: {', '.join(set(templates_used))}")
                
            except Exception as e:
                failed_accounts.append(account['gmail_id'])
                log_email(account['gmail_id'], f"TEST FAILED - {str(e)}")
        
        if total_sent > 0:
            message = f"Test completed! {total_sent} emails sent from {len(test_accounts) - len(failed_accounts)} accounts."
            if failed_accounts:
                message += f" Failed accounts: {', '.join(failed_accounts)}"
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'All test emails failed. Please check your Gmail credentials.'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    init_database()
    load_logs_from_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
