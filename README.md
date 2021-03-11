# Deploying an end-to-end solution on AWS using Amplify

This repository will act as documentation for myself as I deploy a project to AWS. My experiences and notes written here are accurate as of March 2021 and are subject to change in the future. I don't pretend to be an expert but this is guide which outlines the steps that I took to make this work. I welcome any and all feedback.

## The mission

The mission was to deploy a front-end web application written in React Typescript which would collect data from the user, be sent to a machine learning algorithm which will return the prediction using the data inputted, and display this to the user. We also wanted to store the data inputted at the same time as inference was happening. We also needed a way to control who had access to this program.

## The solution

I decided on using AWS Amplify as the way to begin this. It allowed me to host the front-end application and had ready made ties to everything else I needed including database storage and user authentication. I would use AWS Lambda for the machine learning inference as I know that the usage of this application would not warrant an "always on" instance which would cost me more. I used DynamoDB for my datastore which included encryption at rest and finally I utilised Cognito to allow for user authentication.

# Part 1 - Deploying front-end application and setting up CI/CD

For the initial start of this guide, I will be following the tutorial accessible [here](https://aws.amazon.com/getting-started/hands-on/build-react-app-amplify-graphql/). Module 1 of this tutorial works without any hitches and the screenshots are as expected. This will connect Amplify front-end hosting to your (public) GitHub repository and specific branch and will tool up the CI/CD for you so that whenever you push changes to this repo and branch, it will re-deploy your front-end.

# Part 2 - Setting up Amplify CLI and backend environment

A prequisite to this section, **make sure you have a Chromium based browser as your default browser**.

Module 2 in this tutorial is for the most part fine. It will walk you through installing the Amplify CLI (which you do realistically need) on your local machine. Make sure you remember to run `amplify configure` to make sure you can run the next commands. Once your CLI is configured on your local machine you need to head back to your Amplify App page and start your backend environment. This will take a couple minutes. Once this is done, and this is important: **click Open admin UI**. You will then need to return to your terminal window and type in the following command: `amplify pull --appId <given-app-id> --envName staging`. This will connect your app to the just configured backend environment. This command will open a browser tab asking for confirmation. For reasons beyond my cursory knowledge, this confirmation doesn't work in [Safari](https://github.com/aws-amplify/amplify-adminui/issues/84#issuecomment-775399802). **Do not forget to run `amplify push` once you have completed this**

# Part 3 - Setting up user authentication

This is where I start diverging away from the tutorial. The tutorial walks you through the Amplify CLI setup for adding Cognito to the application which is great for getting to grips with but lacks in-depth manual configuration as to how you want people to sign in and sign up. For my uses, I wanted specific options for signing users up and therefore creating my own Cognito User Pool and connecting it to my current Amplify front-end was the easiest solution. For this I used another [tutorial](https://aws.amazon.com/blogs/mobile/use-existing-cognito-resources-for-your-amplify-api-storage-and-more/). The first part of this tutorial walks you through how to create a User Pool and Identity Pool and once you have done this, returning back to the Amplify CLI, and running `amplify import auth` will allow you to connect your app to your customised Cognito setup. When you run this command, make sure you select *Cognito User Pool only* and when prompted, select the the app client with a client secret as your *Native app client*. Again, run `amplify push` to push these changes to your backend and when you return to your Amplify app page, you should see Authentication under your backend environments.

I am using the hosted UI as Cognito makes it very hard to detach the authentication logic from the UI it has built and the easiest way is to just use the hosted UI. To actually use the hosted UI, you will need to add some code to your React application.

In index<span>.<span>js add the following lines of code at the top under your import statements:
```
import Amplify from 'aws-amplify';
import config from './aws-exports';
Amplify.configure(config);
```
In App<span>.<span>js you need to add the following imports:
```
import { withAuthenticator, AmplifySignOut } from '@aws-amplify/ui-react';
```
`AmplifySignOut` allows you to add a sign out button and is just a normal HTML tag `<AmplifySignOut />` and can be placed where you like.

`withAuthenticator` needs to surround your app export at the bottom of App<span>.<span>js like so
```
export default withAuthenticator(App);
```

Once these are done make sure to commit your changes to GitHub and Amplify will rebuild your front-end and redeploy. If like me your build failed, then read on.

## Build failed - You do not have a role attached to your app

I got this error when trying to deploy after setting up the backend. Turns out I need to create an Amplify service IAM role, the guide for which can be found [here](https://docs.aws.amazon.com/amplify/latest/userguide/how-to-service-role-amplify-console.html). Once I had done this, I had to redeploy the front-end and I was back up and running with Cognito Authentication.

# Part 4 - Adding a datastore and API

Back to the original tutorial here, module 4 takes you through step by step as to how to create your database and your API to access it. When creating your API it will prompt you to create the schema and then once completed will create all the boiler plate code for you. The tutorial also provides React JS code for adding and listing all the elements from the database which you can amend for your own purposes. If you want to change the schema after the fact, navigate to your app folder and open the `schema.graphql` file under `/backend/api/<name of app>/`. Once you have changed the schema, you must run `amplify push` to make the changes to the backend and update the boiler plate code. You must then commit and push your work to GitHub to change the front-end work to reflect the new backend changes.

You can check what has been stored to the database by accessing DynamoDB in AWS where there should be a single table with items inside.

The tutorial carries on here to add S3 storage but for my purposes I did not need this.

# Part 5 - Adding ML inference

For ML inference, I decided to use AWS Lambda as I did not need the inference active 24/7 and it was the more cost effective option to run the inference as a serverless service. The model we will be using is a basic scikit-learn model created using the Iris dataset.

When creating a Lambda instance, you can upload a zip file or a zip file stored in S3 storage with all your libraries and packages you need and the code. There is however a limit on the size of this (50MB zip file and 250MB unzipped) and in my exprience it is very easy to go over this. We could also create a Lambda Layer but this is also limited to 250MB limit. For those familiar with Python data science libraries, pandas on its own worked fine as a zip file but adding the scikit-learn package took it straight over the limit. Therefore, the better way to do this is to create a docker image with all your code, model, and libraries. Images are not restricted to the 50MB/250MB limit and are instead limited to 10GB image size which is more than enough for scikit-learn inference.

A lot of tutorials I found for this included model training into the lambda code which I would not be doing as I just needed inference. Therefore I will be approaching this with a model pickle file that needs to be packaged so that I can call the predict function.

Firstly, you will need to create a folder in your local machine which will contain: Python file to handle inference and requests, requirements.txt with your Python packages, Dockerfile, folder which contains your model pickle file. An example is shown below.

![folder structure!](/images/folder_structure.png)

## Python file

Your python file should contain the `handler` function that is called automatically by Lambda when invoked. It should be defined like such:
```
def handler(event, context):
```
Within this function you define the inference as well as the return values from an API request such as the status code, header, and body. You are free to (and should) create other functions but they must be called from inside the `handler` function or else they will never be run. The return value of the `handler` function is essentially a dictionary with the status code, headers, and body that would return from the API (we will be defining the API later) call to the Lambda function. An example is shown below.

![handler return!](/images/return_handler.png)

The Access Control headers are needed to satisfy CORS. Note also that we have added `Authorization` as an allowed header as well as set `Access-Control-Allow-Credentials` to True. This links back to our user authentication and I will discuss this later on.

The body must be in JSON which means if you want to return a pandas dataframe or a numpy array, make sure that they are first converted to JSON either by using the built-in pandas `to_json()` function or `json.dumps` whichever one you are happier with.

## Dockerfile

To build our image to use within Lambda, we need to create a Dockerfile which will outline what Docker needs to include when we build it. Below is the Dockerfile I am using.

![Dockerfile!](/images/dockerfile.png)

`FROM public.ecr.aws/lambda/python:3.7` - This will construct our image from a base image provided by AWS and come with Python 3.7. AWS have a number of base images provided [here](https://github.com/aws/aws-lambda-base-images) and you just change the `python:3.7` part to whichever base image you want to build off of.

`COPY requirements.txt ./tmp/requirements.txt` - This command is the same as the model and app<span>.<span>py lines further down. This essentially copies our local requirements.txt file into our docker image under the tmp folder

`RUN pip install -r ./tmp/requirements.txt` - This runs the pip command from within docker and installs the packages we have defined within our requirements.txt file which we have just copied.

`CMD ["app.handler"]` - This will set the CMD to the `handler` function within our app<span>.<span>py file we looked at earlier

Now we can build our image by typing in `docker build -t <name-of-image> .` and you can check it was created by typing in `docker images`.

## AWS ECR

To get this image into Lambda we have to first upload it to AWS ECR (Elastic Container Registry). We first need to create a repo by clicking *Create repository* in our private ECR repository.

![ECR repository!](/images/ecr.png)

Give your repository a name and confirm the creation. Once created you should see it show up in your list. Access your newly created repo and click *View push commands*

![Push commands!](/images/repo.png)

This will open a dialog box that will talk you through deploying a local image into your repository including authenticating your local Docker client. To do this, make sure you have the AWS CLI installed, instructions for which are found [here](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html).

Once authenticated, you should be able to tag and then push your image that you built above following the instructions provided.

**Note: You will need build, tag, and push everytime you make changes to any file within the Docker image or else these will not be reflected in your Lambda function**

## AWS Lambda function

Once your image has been pushed, we can create the Lambda function. Navigate to the Lambda homepage and select *Functions* on the sidebar. You will likely see a lot of premade functions if this is your first time using AWS and these were automatically created by Amplify.

Click *Create function* and select *Container image* option. Name your function and select the Image from the one you have just pushed and confirm the creation. You can test that your function works by navigating to the Test tab in your function page and invoking a test. If you have configured your Python file to take data in and spit out a prediction then you should see this reflected in the test. Errors here are explanatory and will more times than not be a problem with your Python file.

# Part 6 - Amazon API Gateway

For your front-end application to be able to trigger this ML inference, you need to connect an API to it. We do this using Amazon API Gateway which conveniently works well with Lambda.

Navigate to Amazon API Gateway and click *Create API*. Select the Rest API option, give a name to your API and confirm the creation of the API with all other default settings. In the following screen, click the *Actions* button and select *Create Method*, select *ANY* in the dropdown list and confirm by clicking the small tick button. In the Setup screen make sure *Integration Type* selected is Lambda Function and type your Lambda function name and it should autocomplete and finally Save.

You can now test the API and make sure it works. Chances are that it might not due to CORS issues. Select *ANY* and click *Actions*. In the list select *Enable CORS*, leave the defaults and enable CORS and save. This will now create an *OPTIONS* method but you won't need to touch that.

After all this, you will need to deploy the API also under the *Actions* menu and this should now allow you to call your lambda function via this API. You can test this using Postman or just integrating it into your front-end application and trying to hit it.

# Part 7 - Secure your API Gateway

To prevent everyone with your API URL from accessing your Lambda function, it is important to secure this so that only certain people can access it. I used my Cognito User Pool but there are other ways to do this.

In your newly created API in Amazon API Gateway, select the *Authorizers* option in the sidebar. Give it a name and select Cognito and select your User Pool you created previously. For *Token Source* type in `Authorizer` which matches the Content Header we added back in our Python file, currently running as our Lambda function.

Return back to *Resources* and select *Method Request* under your *ANY* method. Under *Authorization* select the new Authorizer you just created. Finally redeploy your API and now when you try to hit your API via Postman or your front-end it should not work.

To get this API to now work, we need to get a JWT (JSON web token) and send this as our Authorization along with our API request. In your App<span>.<span>js file `import {Auth} from '@aws-amplify'`. You will then need to get the current authenticated user using the following function which will return a Promise.
```
Auth.currentAuthenticatedUser()
    .then(user => {
        axios.get(<API URL>, {
            headers: {
                'Authorization': user.signInUserSession.idToken.jwtToken
            }
        })
        .then(res => {
            data = res.data
            // Do things with the data
        })
    })
```

And now you have a protected API only accessible by people who have login access through your created Cognito User Pool

# Final

This guide should get you from 0 to a full end-to-end ML inference application running entirely on AWS. As prefaced at the start, I am not an expert but through trial and error have created this guide.