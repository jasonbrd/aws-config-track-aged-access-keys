## Notification system for tracking aged access keys

This repo contains the CloudFormation templates required to deploy a notification system which helps track access keys that need rotating. This solution relies on a master account from where you monitor and manage users across multiple target accounts. In each target account, you add an Automatic Remediation to the AWS Config access-keys-rotated rule. The Remediation executes a Systems Manager Automation document, which resolves the user name and then publishes the information to Amazon Simple Notification Service (Amazon SNS) for further processing.

![AccessKeyRotationDiagram](https://user-images.githubusercontent.com/65978123/83672843-edbc9480-a5a4-11ea-898d-9413751e37c2.png)

Here is how the process works:
1.	In every target account, AWS Config executes the rule and invokes the SSM Automation document for every non-compliant resource 
2.	The Automation document does the following actions.
a.	Resolve the user name from the user resourceId through an API call 
b.	Publish a customized message to an SNS topic in the master account



## License

This library is licensed under the MIT-0 License. See the LICENSE file.

