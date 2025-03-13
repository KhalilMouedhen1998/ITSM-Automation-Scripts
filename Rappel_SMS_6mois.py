#Python version - 3.8
#This script requires requests module installed in python.
import requests
 
url = "/api/v3/requests/10972/notifications"
headers ={"authtoken":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
input_data = '''{
    "notification": {
        "subject": "Rappel : Vérification de l'abonnement au fournisseur de SMS",
        "description": "Bonjour, <br><br> Ceci est un rappel pour vérifier l'abonnement auprès du fournisseur de SMS.<br> <br>Cordialement,<br>Support FOCUS",
        "to": [
            {
                "email_id": ""
            },
            {
                "email_id": ""
            },
            {
                "email_id": ""
            }

        ],
        "type": "reply"
    }
}'''
data = {'input_data': input_data}
response = requests.post(url,headers=headers,data=data,verify=False)
print(response.text)
