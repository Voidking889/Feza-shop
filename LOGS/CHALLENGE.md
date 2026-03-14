The following changes were caught up during the testing processes :
# 1.Seller's dashboard:
🚫 couldn't view any of the goods purchased ,dosn't update the dashboard
🚫 in the version 2 of this application {path:[text](d:/Feza_shopv.2.0/seller_dashboard.html)}: it keeps on deriving data from the wrong index file(template file)

# Mitigations
➡️ correct the importing and updating of the dashboard from the time the user immediately purchases without the aid of a 'refresh button' but incase of unseen transctions or slow network caused by heavy traffic-congestion the 'the refresh button' will hence be needed

# 2.💳Feza-Wallet:
🚫problems with the additon of local payment methods such as M-pesa as idea proposed was :Once the user chooses the M-pesa , the user's/client phone number will be asked and a veerification code will be sent to the user's SMS inbox and once verified the system saves the number  in our database (and encrypts the no. via standards of the Service provider ways for maximum protection and privacy and avoid  leaking it to third-parties) -- as per agreement btn the NSP ... and a short prompt will be sent which will ask the user to pay via 'muda wa maongezi' or 'm-pesa - which will 1.redirect to the m-pesa app for secure and trusted payment
                     2. ask the user for his/her m-pesa pin (90-95% assured will use this)' and payment succeds
🚫🏦BANK TRANSFERS :                      
status : 😭😭
# mitigation :
➡️For bank tranfer --- 'ask dad for some help'
➡️ For mobile payment --- 😐



