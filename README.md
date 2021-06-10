# Cloud_Computing_Projects-Spring_2020
 This is a compilation of all 4 cloud computing projects (originally spread across multiple repositories which I collaborated on).

 Note ALL projects were deleted from AWS to avoid monthly billing after the free trial ended. So these applications are not running currently, though the original files are in this repository for viewing. Also, for security purposes, AWS keys have been censored or edited out.

 Each project folder consists of the assignment guidelines, and a folder containing the AWS files and scripts.

## Dining Concierge Client
An Amazon Lex bot which clients chat with through a user interface in order to get restaurant recommendations based on what food they're craving. The bot collects location, cuisine, dining time, number of people in the party, and the client's phone number throughout the conversation. It then uses these parameters to match the client with the appropriate restaurants, sent back as an SNS message to the client's phone number.

Restaurant information was scraped through Yelp, and only includes 5000 Manhattan restaurants, though it can support even more. This data is stored in DynamoDB and an ElasticSearch index for quick querying.

## Smart Door Authentication System
This system uses Kinesis Video Streams and Amazon Rekognition to authenticate people and give them access to a virtual door (representing a real door in an actual scenario). 

An owner and visitor each access the system through different front ends. A visitor is seen through a video doorbell and has their face identified by Rekognition. Unknown visitors will alert the owner, and the owner can deny or approve their access through a simple user interface. 

Approved visitors get an OTP sent to their phones which they use to open the virtual door. Approved visitors also have a face id created and stored in the database so they can automatically get OTPs next time they come.

DynamoDB stores one time passcodes and visitor information (id, face images, names, phone numbers).

## Photo Album Application
An online photo album, similar to google images, which lets clients upload various images and search them. Searching can also be done with voice commands (e.g "find me pictures of cute puppies"). Voice commands picks up keywords for image descriptions through Amazon Lex.

Uploaded photos will be indexed with description keyword tags identified through AWS Rekognition. This information is stored in ElasticSearch. Queries search images up in ElasticSearch by description keywords and return them to the user.

## Email Spam Detection
Uses Amazon Sagemaker's machine learning platform to identify spam email. Emails addresses added to the system will have their incoming messages be predicted as spam or not. The results are emailed back as a reply, and include confidence levels (e.g "78% sure this message is spam").