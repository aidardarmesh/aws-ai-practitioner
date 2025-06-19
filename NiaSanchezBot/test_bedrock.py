#!/usr/bin/env python3
"""
Simple test script to verify Bedrock connectivity and model access
"""
import boto3
import json
from botocore.exceptions import ClientError

def test_bedrock_connection():
    """Test basic Bedrock connectivity"""
    try:
        # Initialize Bedrock client
        bedrock_client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1"
        )
        
        # Test with Titan Text Express
        model_id = "amazon.titan-text-express-v1"
        prompt = "Hello, this is a test. Please respond with a simple greeting."
        
        # Prepare the request body for Titan
        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 100,
                "temperature": 0.7,
                "topP": 0.9
            }
        })
        
        print(f"Testing Bedrock model: {model_id}")
        print(f"Prompt: {prompt}")
        print("-" * 50)
        
        # Make the API call
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        generated_text = response_body['results'][0]['outputText']
        
        print("✅ SUCCESS!")
        print(f"Response: {generated_text}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS ClientError: {error_code}")
        print(f"Message: {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("\n🔧 SOLUTION: You need to add Bedrock permissions to your Lambda function's IAM role")
            print("The SAM template has been updated with the necessary permissions.")
            print("Run 'sam deploy' to apply the changes.")
        elif error_code == 'ValidationException':
            print("\n🔧 SOLUTION: Check if the model ID is correct and available in your region")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_nova_micro():
    """Test with the newer Nova Micro model"""
    try:
        bedrock_client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1"
        )
        
        model_id = "amazon.nova-micro-v1:0"
        
        # Nova uses a different request format
        messages = [
            {
                "role": "user",
                "content": [{"text": "Hello, this is a test with Nova Micro. Please respond briefly."}]
            }
        ]
        
        body = json.dumps({
            "messages": messages,
            "inferenceConfig": {
                "max_new_tokens": 100,
                "temperature": 0.7
            }
        })
        
        print(f"\nTesting newer model: {model_id}")
        print("-" * 50)
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        generated_text = response_body['output']['message']['content'][0]['text']
        
        print("✅ SUCCESS with Nova Micro!")
        print(f"Response: {generated_text}")
        return True
        
    except Exception as e:
        print(f"❌ Nova Micro test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Bedrock LLM Access")
    print("=" * 50)
    
    # Test basic Titan model
    titan_success = test_bedrock_connection()
    
    # Test newer Nova model
    nova_success = test_nova_micro()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"Titan Text Express: {'✅ Working' if titan_success else '❌ Failed'}")
    print(f"Nova Micro: {'✅ Working' if nova_success else '❌ Failed'}")
    
    if titan_success or nova_success:
        print("\n🎉 At least one model is working! Your Bedrock setup is ready.")
        print("You can now deploy your Lambda function with 'sam deploy'")
    else:
        print("\n⚠️  No models are working. Please check your AWS credentials and permissions.")
