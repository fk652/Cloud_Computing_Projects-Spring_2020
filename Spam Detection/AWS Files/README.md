# cs9223g-hw4-spam-detection

## *Note this project is no longer accessible/working

Spam detection

1. Before sending any emails, make sure to verify our domain "mynox.tech" on SES first.
2. Once our domain is verified, you can build the cloudformation template.
3. The default email parameter for sending spam emails to is "hw4-emails@mail.mynox.tech" when building the template
   * You can also specify the sagemaker endpoint as a parameter
4. Make sure your own email (the sender) is verified on SES email addresses before sending an email.
5. Once everything is verified, send an email to "hw4-emails@mail.mynox.tech" and wait a few minutes for the spam detection reply.


Cloudformation Deployment

Serverless Package doesn't accept Local CodeUri. Upload the Lambda Function on S3 first. 

``` aws cloudformation package --template s3_ses.yaml --s3-bucket myhw-email-bucket --output yaml > packaged-template.yml ```

Then use the template ```packaged-template.yml``` to deploy Cloudformation Stack. 

``` aws cloudformation deploy --template packaged-template.yml --stack-name hw4stack --capabilities CAPABILITY_IAM```
