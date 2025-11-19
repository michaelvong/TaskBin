# TaskBin
run buildmain.py to bring up all aws resources, run deletemain.py to delete all the resources, <br />
in CreateLambdas.py the "LAMBDA_ROLE_ARN" must be set to your correct lambdas permissions that allow the right policies <br />
<br /> 
after full build, there will be an API endpoint. That will be ur base url that will be used to call all endpoints <br />
for example: https://44iiv17g08.execute-api.us-west-1.amazonaws.com/prod <br />
example route call using this base url: https://44iiv17g08.execute-api.us-west-1.amazonaws.com/prod/boards/82f13a29-4ffd-4076-8d49-bfd22a0f4df8/join