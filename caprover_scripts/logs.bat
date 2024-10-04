@REM Show logs of the app
ssh -i "D:/aws/ec2/daridev-login.pem" ubuntu@ec2-3-12-224-160.us-east-2.compute.amazonaws.com "sudo docker service logs srv-captain--nyx-dashboard --since 10m --follow"