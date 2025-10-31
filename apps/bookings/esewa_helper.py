import hashlib
import hmac
import base64
from django.conf import settings


class SimpleEsewaPayment:
    """
    Simple eSewa payment helper that doesn't require external dependencies
    """
    
    def __init__(self, amount, tax_amount=0, total_amount=None, product_service_charge=0, 
                 transaction_uuid=None, product_delivery_charge=0, success_url=None, failure_url=None):
        self.amount = str(amount)
        self.tax_amount = str(tax_amount)
        self.total_amount = str(total_amount or amount)
        self.product_service_charge = str(product_service_charge)
        self.transaction_uuid = str(transaction_uuid)
        self.product_delivery_charge = str(product_delivery_charge)
        self.success_url = success_url
        self.failure_url = failure_url
        self.secret_key = getattr(settings, 'ESEWA_SECRET_KEY', 'NePaLiGuIdE!@#')
        self.merchant_id = getattr(settings, 'ESEWA_MERCHANT_ID', 'EPAYTEST')
        
    def create_signature(self, transaction_uuid=None):
        """
        Create signature for eSewa payment
        """
        if transaction_uuid:
            self.transaction_uuid = str(transaction_uuid)
            
        # Create signature string
        signature_string = f"total_amount={self.total_amount},transaction_uuid={self.transaction_uuid},product_code={self.merchant_id}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        self.signature = base64.b64encode(signature).decode('utf-8')
        return self.signature
    
    def generate_form(self):
        """
        Generate HTML form for eSewa payment
        """
        # Create signature
        self.create_signature()
        
        form_html = f'''
        <form action="https://rc-epay.esewa.com.np/api/epay/main/v2/form" method="POST" style="display: none;" id="esewaForm">
            <input type="hidden" name="amount" value="{self.amount}">
            <input type="hidden" name="tax_amount" value="{self.tax_amount}">
            <input type="hidden" name="total_amount" value="{self.total_amount}">
            <input type="hidden" name="transaction_uuid" value="{self.transaction_uuid}">
            <input type="hidden" name="product_code" value="{self.merchant_id}">
            <input type="hidden" name="product_service_charge" value="{self.product_service_charge}">
            <input type="hidden" name="product_delivery_charge" value="{self.product_delivery_charge}">
            <input type="hidden" name="success_url" value="{self.success_url}">
            <input type="hidden" name="failure_url" value="{self.failure_url}">
            <input type="hidden" name="signed_field_names" value="total_amount,transaction_uuid,product_code">
            <input type="hidden" name="signature" value="{self.signature}">
        </form>
        '''
        
        return form_html
    
    def is_completed(self, verify_payment=False):
        """
        Check if payment is completed
        For demo purposes, this always returns True
        In production, you would verify with eSewa API
        """
        if verify_payment:
            # In production, make API call to eSewa to verify payment
            # For demo purposes, return True
            return True
        return True