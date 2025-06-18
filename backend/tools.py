import re
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
import logging


# Step 1: Define the reset password tool
class ResetPassword(BaseModel):
    username: str = Field(..., description="username provided by the user to reset the password")

# Step 2: Define the actual logic function
def reset_password_fn(username: str) -> str:
    logging.info(f"Resetting password for {username}")
    if not username.strip():
        return "Username is required to reset the password."
    if len(username) < 3:
        return "Username must be at least 3 characters long."
    return f"Password reset instructions have been sent to the registered email for user '{username}'."

# Step 3: Convert the logic function into a structured tool
reset_password = StructuredTool.from_function(
    name="reset_password",
    func=reset_password_fn,
    args_schema=ResetPassword,
    description="Resets the password for a given username"
)


# Create a structured tool for account creation using Pydantic for input validation
# Step 1: Define the input schema using Pydantic
class CreateAccountInput(BaseModel):
    name: str = Field(..., description="Full name of the user")
    email: str = Field(..., description="User's email address in valid format")

# Step 2: Define the actual logic function
def create_account_fn(name: str, email: str) -> str:
    logging.info(f"Creating account for {name} with email {email}")
    if not name.strip():
        return "Please provide a valid full name."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return "Invalid email format. Please enter a valid email address."
    if email.endswith("@example.com"):
        return "Please provide a real email address, not a placeholder."
    return f"Account created successfully for {name}. A confirmation has been sent to {email}."

# Step 3: Convert the logic function into a structured tool
create_account = StructuredTool.from_function(
    name="create_account",
    func=create_account_fn,
    args_schema=CreateAccountInput,
    description="Creates a user account using full name and email address"
)

# get_billing_info tool
# Step 1: Define the input schema using Pydantic
class GetBillingInfo(BaseModel):
    account_id: str =  Field(..., description="account id of the user")

# Step 2: Define the actual logic function
def get_billing_info_fn(account_id: str) -> str:
    logging.info(f"Retrieving billing info for account id: {account_id}")
    if not account_id.strip():
        return "Account ID is required to retrieve billing information."
    if not re.match(r"^[A-Za-z0-9_-]{4,}$", account_id):
        return "Invalid account ID format. It should be alphanumeric with at least 4 characters."

    return f"The billing balance for {account_id} is $49.95, due by the 15th of this month."

# step 3: Convert the logic function into a structured tool
get_billing_info = StructuredTool.from_function(
    name="get_billing_info",
    func=get_billing_info_fn,
    args_schema=GetBillingInfo,
    description="Retrieves billing information for a given account ID"
)
# Ensure the tools are registered and can be used by the agent
# __all__ = ["create_account", "reset_password", "get_billing_info"]
# This ensures that the tools can be imported and used in other parts of the application.