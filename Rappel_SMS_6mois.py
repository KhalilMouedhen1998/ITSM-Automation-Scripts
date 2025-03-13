#Python version - 3.8
#This script requires requests module installed in python.
import requests
 
url = "https://service-desk.focus-corporation.com/api/v3/requests/10972/notifications"
headers ={"authtoken":"906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}
input_data = '''{
    "notification": {
        "subject": "Rappel : Vérification de l'abonnement au fournisseur de SMS",
        "description": "Bonjour, <br><br> Ceci est un rappel pour vérifier l'abonnement auprès du fournisseur de SMS.<br> <br>Cordialement,<br>Support FOCUS",
        "to": [
            {
                "email_id": "khalil.mouadhen@focus-corporation.com"
            },
            {
                "email_id": "khalil.naoui@focus-corporation.com"
            },
            {
                "email_id": "medhoussein.sayah@focus-corporation.com"
            }

        ],
        "type": "reply"
    }
}'''
data = {'input_data': input_data}
response = requests.post(url,headers=headers,data=data,verify=False)
print(response.text)
