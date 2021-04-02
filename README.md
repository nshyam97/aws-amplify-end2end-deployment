# Deploying an end-to-end solution on AWS using Amplify

This repository will act as documentation for myself as I deploy a project to AWS. My experiences and notes written here are accurate as of March 2021 and are subject to change in the future. I don't pretend to be an expert but this is guide which outlines the steps that I took to make this work. I welcome any and all feedback.

## The mission

The mission was to deploy a front-end web application written in React Typescript which would collect data from the user, be sent to a machine learning algorithm which will return the prediction using the data inputted, and display this to the user. I also wanted to store the data inputted at the same time as inference was happening. I also needed a way to control who had access to this program.

## The solution

I decided on using AWS Amplify as the way to begin this. It allowed me to host the front-end application and had ready made ties to everything else I needed including database storage and user authentication. I would use AWS Lambda for the machine learning inference as I know that the usage of this application would not warrant an "always on" instance which would cost me more. I used DynamoDB for my datastore which included encryption at rest and finally I utilised Cognito to allow for user authentication.

# Part 1 - Deploying front-end application and setting up CI/CD

For the initial start of this guide, I will be following the tutorial accessible [here](https://aws.amazon.com/getting-started/hands-on/build-react-app-amplify-graphql/). Module 1 of this tutorial works without any hitches and the screenshots are as expected. This will connect Amplify front-end hosting to your (public) GitHub repository and specific branch and will tool up the CI/CD for you so that whenever you push changes to this repo and branch, it will re-deploy your front-end.

# Part 2 - Setting up Amplify CLI backend environment

Module 2 in this tutorial works for new projects but is a real issue when trying to import auth rather than adding auth using the amplify CLI. Once you have installed the Amplify CLI, run `amplify configure`. Follow the steps to create the IAM user and note the ID and key. The tutuorial takes you through creating the backend from the Amplify website. This I found, caused many issue when I wanted to add my pre-made cognito user pools. For this, we need the amplify appId and the CLI. Navigate to your frontend amplify homepage and select **General** under App Settings in the sidebar. Under App ARN you will find your ARN, the appId is the string after the last forward slash of this ARN. Copy this.

Navigate back to your Amplify CLI and type `amplify init --appId <appId>`. This will configure the application backend from your CLI and make it possible to import auth. We will finish this in the next section so don't commit or push anything yet.

# Part 3 - Setting up user authentication and completing backend

Once you have performed the `amplify init` command, we can import auth. Make sure you have an existing user pool ready to import. I used this [tutorial](https://aws.amazon.com/blogs/mobile/use-existing-cognito-resources-for-your-amplify-api-storage-and-more/) to create my user pool and federated identities. Once you have created the user pools and federated identity, type `amplify import auth` into the CLI. In the following options, select *Cognito User Pool only* and when prompted, select the app client with a client secret as your *Native app client*. And that's cognito imported locally, finish this process by pushing your changes using `amplify push --y`. Heading back to the original tutorial and [module 3](https://aws.amazon.com/getting-started/hands-on/build-react-app-amplify-graphql/module-three/), install the amplify libraries using `npm install aws-amplify @aws-amplify/ui-react` and add the react code to your application. In case this tutorial disappears sometime in the future the code is shown here:

*index.js*
```
import Amplify from 'aws-amplify';
import config from './aws-exports';
Amplify.configure(config);
```

*App.js*
```
import React from 'react';
import logo from './logo.svg';
import './App.css';
import { withAuthenticator, AmplifySignOut } from '@aws-amplify/ui-react'

function App() {
  return (
    <div className="App">
      <header>
        <img src={logo} className="App-logo" alt="logo" />
        <h1>We now have Auth!</h1>
      </header>
      <AmplifySignOut />
    </div>
  );
}

export default withAuthenticator(App);
```
**Note: Do not push your git changes yet because this will fail your build.**

Because we added the backend separately, we need to update our build script to take into account our newly created backend and connect it to our frontend. Navigate to **Build Settings** in the sidebar under App settings and edit the amplify.yml to the following (also available on the tutorial):

*amplify.yml*
```
version: 1
backend:
  phases:
    build:
      commands:
        - '# Execute Amplify CLI with the helper script'
        - amplifyPush --simple
frontend:
  phases:
    preBuild:
      commands:
        - yarn install
    build:
      commands:
        - yarn run build
  artifacts:
    baseDirectory: build
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```
Navigate back to your frontend page and click the **Edit** button and connect your frontend to your backend you created.

![connect to backend!](/images/connect.png)

Again due to creating our backend separately and importing auth, our amplify environment variables have not been added to support auth. We need to do this manually. Navigate to **Environment variables** in the sidebar under App settings and click *Manage variables*. We need to add 3 variables for auth to build successfully: **AMPLIFY_USERPOOL_ID**, **AMPLIFY_WEBCLIENT_ID**, and **AMPLIFY_NATIVECLIENT_ID**. When we configured and initialised amplify in our project in the previous step, you will see that they added a new **amplify** folder to your application directory. You will find all of these variables under the *team-provider-info.json* file. Copy the values into the environment variables for the corresponding variables and save.

One more step before we cna push our git changes. We will need to add a service role to our amplify app to make sure the backend resources can be accessed. The following [tutorial](https://docs.aws.amazon.com/amplify/latest/userguide/how-to-service-role-amplify-console.html) walks you through the entire process including adding it to your amplify project.

You can now git push your changes and this will trigger a new amplify build. Once completed this should result in your application having auth with the specific user pool you created.

# Part 4 - Adding a datastore and API

Back to the original tutorial here, module 4 takes you through step by step as to how to create your database and your API to access it. When creating your API it will prompt you to create the schema and then once completed will create all the boiler plate code for you. The tutorial also provides React JS code for adding and listing all the elements from the database which you can amend for your own purposes. If you want to change the schema after the fact, navigate to your app folder and open the `schema.graphql` file under `/backend/api/<name of app>/`. Once you have changed the schema, you must run `amplify push` to make the changes to the backend and update the boiler plate code. You must then commit and push your work to GitHub to change the front-end work to reflect the new backend changes.

You can check what has been stored to the database by accessing DynamoDB in AWS where there should be a single table with items inside.

I have to secure this GraphQL API as well so that not anyone can create, delete or access the datastore. I secured this using the Cognito User Pool I created earlier and for this I needed to install the AWS AppSync SDK. You can install this SDK using `npm install --save aws-appsync`. We then need to add some code to get the JWT to send in our authorization header.

```
import AWSAppSyncClient, { AUTH_TYPE } from 'aws-appsync';
import awsconfig from './aws-exports';

Amplify.configure(awsconfig);

const client = new AWSAppSyncClient({
  url: awsconfig.aws_appsync_graphqlEndpoint,
  region: awsconfig.aws_appsync_region,
  auth: {
    type: AUTH_TYPE.AMAZON_COGNITO_USER_POOLS,
    jwtToken: async () => (await Auth.currentSession()).getIdToken().getJwtToken(),
  },
});
```

This will get the JWT and set out authentication type to use Cognito User Pool. We also need to change 2 more files to reflect these changes, `aws-export.js` and `backend-config.json`. In `aws-export.js`, the `"aws_appsync_authenticationType"` field is populated with `API_KEY` and we need to change this to `AMAZON_COGNITO_USER_POOLS`. We need to add the same thing to `backend-config.json` for the `authenticationType` field under `defaultAuthentication`.

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
