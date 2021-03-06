﻿from bingads.service_client import ServiceClient
from bingads.authorization import *
from bingads.v10 import *
from bingads.v10.bulk import *

import sys
import webbrowser
from time import gmtime, strftime
from suds import WebFault

# Optionally you can include logging to output traffic, for example the SOAP request and response.

#import logging
#logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

if __name__ == '__main__':
    print("Python loads the web service proxies at runtime, so you will observe " \
          "a performance delay between program launch and main execution...\n")

    DEVELOPER_TOKEN='DeveloperTokenGoesHere'
    ENVIRONMENT='production'
    
    # If you are using OAuth in production, CLIENT_ID is required and CLIENT_STATE is recommended.
    CLIENT_ID='ClientIdGoesHere'
    CLIENT_STATE='ClientStateGoesHere'

    APP_AD_EXTENSION_ID_KEY=-11
    CALL_AD_EXTENSION_ID_KEY=-12
    CALLOUT_AD_EXTENSION_ID_KEY=-13
    LOCATION_AD_EXTENSION_ID_KEY=-14
    REVIEW_AD_EXTENSION_ID_KEY=-15
    SITE_LINK_AD_EXTENSION_ID_KEY=-16
    CAMPAIGN_ID_KEY=-123

    # The directory for the bulk files.
    FILE_DIRECTORY='c:/bulk/'

    # The name of the bulk download file.
    DOWNLOAD_FILE_NAME='download.csv'

    #The name of the bulk upload file.
    UPLOAD_FILE_NAME='upload.csv'

    # The name of the bulk upload result file.
    RESULT_FILE_NAME='result.csv'

    # The bulk file extension type.
    FILE_FORMAT = DownloadFileType.csv

    # The bulk file extension type as a string.
    FILE_TYPE = 'Csv'

    authorization_data=AuthorizationData(
        account_id=None,
        customer_id=None,
        developer_token=DEVELOPER_TOKEN,
        authentication=None,
    )
      
    # Take advantage of the BulkServiceManager class to efficiently manage ads and keywords for all campaigns in an account. 
    # The client library provides classes to accelerate productivity for downloading and uploading entities. 
    # For example the upload_entities method of the BulkServiceManager class submits your upload request to the bulk service, 
    # polls the service until the upload completed, downloads the result file to a temporary directory, and exposes BulkEntity-derived objects  
    # that contain close representations of the corresponding Campaign Management data objects and value sets.

    # Poll for downloads at reasonable intervals. You know your data better than anyone. 
    # If you download an account that is well less than one million keywords, consider polling 
    # at 15 to 20 second intervals. If the account contains about one million keywords, consider polling 
    # at one minute intervals after waiting five minutes. For accounts with about four million keywords, 
    # consider polling at one minute intervals after waiting 10 minutes. 
    
    bulk_service=BulkServiceManager(
        authorization_data=authorization_data, 
        poll_interval_in_milliseconds=5000, 
        environment=ENVIRONMENT,
    )

    campaign_service=ServiceClient(
        service='CampaignManagementService', 
        authorization_data=authorization_data, 
        environment=ENVIRONMENT,
        version=10,
    )

    customer_service=ServiceClient(
        'CustomerManagementService', 
        authorization_data=authorization_data, 
        environment=ENVIRONMENT,
        version=9,
    )

def authenticate_with_username():
    ''' 
    Sets the authentication property of the global AuthorizationData instance with PasswordAuthentication.
    '''
    global authorization_data
    authentication=PasswordAuthentication(
        user_name='UserNameGoesHere',
        password='PasswordGoesHere'
    )

    # Assign this authentication instance to the global authorization_data. 
    authorization_data.authentication=authentication
 
def authenticate_with_oauth():
    ''' 
    Sets the authentication property of the global AuthorizationData instance with OAuthDesktopMobileAuthCodeGrant.
    '''
    global authorization_data

    authentication=OAuthDesktopMobileAuthCodeGrant(
        client_id=CLIENT_ID
    )

    # It is recommended that you specify a non guessable 'state' request parameter to help prevent
    # cross site request forgery (CSRF). 
    authentication.state=CLIENT_STATE

    # Assign this authentication instance to the global authorization_data. 
    authorization_data.authentication=authentication   

    # Register the callback function to automatically save the refresh token anytime it is refreshed.
    # Uncomment this line if you want to store your refresh token. Be sure to save your refresh token securely.
    authorization_data.authentication.token_refreshed_callback=save_refresh_token
    
    refresh_token=get_refresh_token()
    
    try:
        # If we have a refresh token let's refresh it
        if refresh_token is not None:
            authorization_data.authentication.request_oauth_tokens_by_refresh_token(refresh_token)
        else:
            request_user_consent()
    except OAuthTokenRequestException:
        # The user could not be authenticated or the grant is expired. 
        # The user must first sign in and if needed grant the client application access to the requested scope.
        request_user_consent()
    
def request_user_consent():
    global authorization_data

    webbrowser.open(authorization_data.authentication.get_authorization_endpoint(), new=1)
    # For Python 3.x use 'input' instead of 'raw_input'
    if(sys.version_info.major >= 3):
        response_uri=input(
            "You need to provide consent for the application to access your Bing Ads accounts. " \
            "After you have granted consent in the web browser for the application to access your Bing Ads accounts, " \
            "please enter the response URI that includes the authorization 'code' parameter: \n"
        )
    else:
        response_uri=raw_input(
            "You need to provide consent for the application to access your Bing Ads accounts. " \
            "After you have granted consent in the web browser for the application to access your Bing Ads accounts, " \
            "please enter the response URI that includes the authorization 'code' parameter: \n"
        )

    if authorization_data.authentication.state != CLIENT_STATE:
       raise Exception("The OAuth response state does not match the client request state.")

    # Request access and refresh tokens using the URI that you provided manually during program execution.
    authorization_data.authentication.request_oauth_tokens_by_response_uri(response_uri=response_uri) 

def get_refresh_token():
    ''' 
    Returns a refresh token if stored locally.
    '''
    file=None
    try:
        file=open("refresh.txt")
        line=file.readline()
        file.close()
        return line if line else None
    except IOError:
        if file:
            file.close()
        return None

def save_refresh_token(oauth_tokens):
    ''' 
    Stores a refresh token locally. Be sure to save your refresh token securely.
    '''
    with open("refresh.txt","w+") as file:
        file.write(oauth_tokens.refresh_token)
        file.close()
    return None

def search_accounts_by_user_id(user_id):
    ''' 
    Search for account details by UserId.
    
    :param user_id: The Bing Ads user identifier.
    :type user_id: long
    :return: List of accounts that the user can manage.
    :rtype: ArrayOfAccount
    '''
    global customer_service
   
    paging={
        'Index': 0,
        'Size': 10
    }

    predicates={
        'Predicate': [
            {
                'Field': 'UserId',
                'Operator': 'Equals',
                'Value': user_id,
            },
        ]
    }

    search_accounts_request={
        'PageInfo': paging,
        'Predicates': predicates
    }
        
    return customer_service.SearchAccounts(
        PageInfo=paging,
        Predicates=predicates
    )

def print_percent_complete(progress):
    output_status_message("Percent Complete: {0}\n".format(progress.percent_complete))

def output_bulk_campaigns(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCampaign: \n")
        output_status_message("AccountId: {0}".format(entity.account_id))
        output_status_message("ClientId: {0}".format(entity.client_id))

        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))

        output_bulk_performance_data(entity.performance_data)
        output_bulk_quality_score_data(entity.quality_score_data)

        # Output the Campaign Management Campaign Object
        output_campaign(entity.campaign)

        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')

def output_campaign(campaign):
    if campaign is not None:
        output_status_message("BudgetType: {0}".format(campaign.BudgetType))
        if campaign.CampaignType is not None:
            for campaign_type in campaign.CampaignType:
                output_status_message("CampaignType: {0}".format(campaign_type))
        else:
            output_status_message("CampaignType: None")
        output_status_message("DailyBudget: {0}".format(campaign.DailyBudget))
        output_status_message("Description: {0}".format(campaign.Description))
        output_status_message("ForwardCompatibilityMap: ")
        if campaign.ForwardCompatibilityMap is not None and len(campaign.ForwardCompatibilityMap.KeyValuePairOfstringstring) > 0:
            for pair in campaign.ForwardCompatibilityMap:
                output_status_message("Key: {0}".format(pair.key))
                output_status_message("Value: {0}".format(pair.value))
        output_status_message("Id: {0}".format(campaign.Id))
        output_status_message("MonthlyBudget: {0}".format(campaign.MonthlyBudget))
        output_status_message("Name: {0}".format(campaign.Name))
        output_status_message("NativeBidAdjustment: {0}".format(campaign.NativeBidAdjustment))
        output_status_message("Settings: ")
        for setting in campaign.Settings.Setting:
            if setting.Type == 'ShoppingSetting':
                output_status_message("\tShoppingSetting: ")
                output_status_message("\t\tPriority: {0}".format(setting.Priority))
                output_status_message("\t\tSalesCountryCode: {0}".format(setting.SalesCountryCode))
                output_status_message("\t\tStoreId: {0}".format(setting.StoreId))
        output_status_message("Status: {0}".format(campaign.Status))
        output_status_message("TimeZone: {0}".format(campaign.TimeZone))
        output_status_message("TrackingUrlTemplate: {0}".format(campaign.TrackingUrlTemplate))
        output_status_message("UrlCustomParameters: ")
        if campaign.UrlCustomParameters is not None and campaign.UrlCustomParameters.Parameters is not None:
            for custom_parameter in campaign.UrlCustomParameters.Parameters['CustomParameter']:
                output_status_message("\tKey: {0}".format(custom_parameter.Key))
                output_status_message("\tValue: {0}".format(custom_parameter.Value))

def output_bulk_app_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkAppAdExtension: \n")
        output_status_message("Account Id: {0}".format(entity.account_id))
        output_status_message("Client Id: {0}".format(entity.client_id))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))

        # Output the Campaign Management AppAdExtension Object
        output_app_ad_extension(entity.app_ad_extension)

        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_bulk_campaign_app_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCampaignAppAdExtension: \n")
        if entity.ad_extension_id_to_entity_id_association is not None:
            output_status_message("AdExtensionId: {0}".format(entity.ad_extension_id_to_entity_id_association.AdExtensionId))
            output_status_message("EntityId: {0}".format(entity.ad_extension_id_to_entity_id_association.EntityId))
        output_status_message("Campaign Name: {0}".format(entity.campaign_name))
        output_status_message("Client Id: {0}".format(entity.client_id))
        output_status_message("Editorial Status: {0}".format(entity.editorial_status))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))
        output_status_message("Status: {0}".format(entity.status))
        
        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
                
def output_bulk_call_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCallAdExtension: \n")
        output_status_message("Account Id: {0}".format(entity.account_id))
        output_status_message("Client Id: {0}".format(entity.client_id))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))

        # Output the Campaign Management CallAdExtension Object
        output_call_ad_extension(entity.call_ad_extension)

        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_bulk_campaign_call_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCampaignCallAdExtension: \n")
        if entity.ad_extension_id_to_entity_id_association is not None:
            output_status_message("AdExtensionId: {0}".format(entity.ad_extension_id_to_entity_id_association.AdExtensionId))
            output_status_message("EntityId: {0}".format(entity.ad_extension_id_to_entity_id_association.EntityId))
        output_status_message("Campaign Name: {0}".format(entity.campaign_name))
        output_status_message("Client Id: {0}".format(entity.client_id))
        output_status_message("Editorial Status: {0}".format(entity.editorial_status))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))
        output_status_message("Status: {0}".format(entity.status))
        
        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')

def output_bulk_callout_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCalloutAdExtension: \n")
        output_status_message("Account Id: {0}".format(entity.account_id))
        output_status_message("Client Id: {0}".format(entity.client_id))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))

        # Output the Campaign Management CalloutAdExtension Object
        output_callout_ad_extension(entity.callout_ad_extension)

        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_bulk_campaign_callout_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCampaignCalloutAdExtension: \n")
        if entity.ad_extension_id_to_entity_id_association is not None:
            output_status_message("AdExtensionId: {0}".format(entity.ad_extension_id_to_entity_id_association.AdExtensionId))
            output_status_message("EntityId: {0}".format(entity.ad_extension_id_to_entity_id_association.EntityId))
        output_status_message("Campaign Name: {0}".format(entity.campaign_name))
        output_status_message("Client Id: {0}".format(entity.client_id))
        output_status_message("Editorial Status: {0}".format(entity.editorial_status))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))
        output_status_message("Status: {0}".format(entity.status))
        
        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_bulk_location_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkLocationAdExtension: \n")
        output_status_message("Account Id: {0}".format(entity.account_id))
        output_status_message("Client Id: {0}".format(entity.client_id))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))

        # Output the Campaign Management LocationAdExtension Object
        output_location_ad_extension(entity.location_ad_extension)

        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_bulk_campaign_location_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCampaignLocationAdExtension: \n")
        if entity.ad_extension_id_to_entity_id_association is not None:
            output_status_message("AdExtensionId: {0}".format(entity.ad_extension_id_to_entity_id_association.AdExtensionId))
            output_status_message("EntityId: {0}".format(entity.ad_extension_id_to_entity_id_association.EntityId))
        output_status_message("Campaign Name: {0}".format(entity.campaign_name))
        output_status_message("Client Id: {0}".format(entity.client_id))
        output_status_message("Editorial Status: {0}".format(entity.editorial_status))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))
        output_status_message("Status: {0}".format(entity.status))
        
        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')

def output_bulk_review_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkReviewAdExtension: \n")
        output_status_message("Account Id: {0}".format(entity.account_id))
        output_status_message("Client Id: {0}".format(entity.client_id))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))

        # Output the Campaign Management ReviewAdExtension Object
        output_review_ad_extension(entity.review_ad_extension)

        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_bulk_campaign_review_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCampaignReviewAdExtension: \n")
        if entity.ad_extension_id_to_entity_id_association is not None:
            output_status_message("AdExtensionId: {0}".format(entity.ad_extension_id_to_entity_id_association.AdExtensionId))
            output_status_message("EntityId: {0}".format(entity.ad_extension_id_to_entity_id_association.EntityId))
        output_status_message("Campaign Name: {0}".format(entity.campaign_name))
        output_status_message("Client Id: {0}".format(entity.client_id))
        output_status_message("Editorial Status: {0}".format(entity.editorial_status))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))
        output_status_message("Status: {0}".format(entity.status))
        
        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
                
def output_bulk_site_link_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkSiteLinkAdExtension: \n")
        output_status_message("Account Id: {0}".format(entity.account_id))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))

        # Output the Campaign Management SiteLinksAdExtension Object
        output_site_links_ad_extension(entity.site_links_ad_extension)

        if entity.site_links is not None and len(entity.site_links) > 0:
            output_bulk_site_links(entity.site_links)

        output_status_message('')

def output_bulk_site_links(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkSiteLink: \n")
        output_status_message("Account Id: {0}".format(entity.account_id))
        output_status_message("Ad Extension Id: {0}".format(entity.ad_extension_id))
        output_status_message("Client Id: {0}".format(entity.client_id))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))
        output_status_message("Order: {0}".format(entity.order))
        output_status_message("Status: {0}".format(entity.status))
        output_status_message("Version: {0}".format(entity.version))
        
        # Output the Campaign Management SiteLink Object
        output_site_links([entity.site_link])

        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_bulk_campaign_site_link_ad_extensions(bulk_entities):
    for entity in bulk_entities:
        output_status_message("BulkCampaignSiteLinkAdExtension: \n")
        if entity.ad_extension_id_to_entity_id_association is not None:
            output_status_message("AdExtensionId: {0}".format(entity.ad_extension_id_to_entity_id_association.AdExtensionId))
            output_status_message("EntityId: {0}".format(entity.ad_extension_id_to_entity_id_association.EntityId))
        output_status_message("Campaign Name: {0}".format(entity.campaign_name))
        output_status_message("Client Id: {0}".format(entity.client_id))
        output_status_message("Editorial Status: {0}".format(entity.editorial_status))
        if entity.last_modified_time is not None:
            output_status_message("LastModifiedTime: {0}".format(entity.last_modified_time))
        output_status_message("Status: {0}".format(entity.status))
        
        if entity.has_errors:
            output_bulk_errors(entity.errors)

        output_status_message('')
        
def output_app_ad_extension(extension):
    if extension is not None:
        output_status_message("Id: {0}".format(extension.Id))
        output_status_message("Type: {0}".format(extension.Type))
        output_status_message("AppPlatform: {0}".format(extension.AppPlatform))
        output_status_message("AppStoreId: {0}".format(extension.AppStoreId))
        output_status_message("DestinationUrl: {0}".format(extension.DestinationUrl))
        output_status_message("DevicePreference: {0}".format(extension.DevicePreference))
        output_status_message("DisplayText: {0}".format(extension.DisplayText))
        output_status_message("Status: {0}".format(extension.Status))
        output_status_message("Version: {0}".format(extension.Version))
        output_status_message('')

def output_call_ad_extension(extension):
    if extension is not None:
        output_status_message("Id: {0}".format(extension.Id))
        output_status_message("Type: {0}".format(extension.Type))
        output_status_message("CountryCode: {0}".format(extension.CountryCode))
        output_status_message("DevicePreference: {0}".format(extension.DevicePreference))
        output_status_message("IsCallOnly: {0}".format(extension.IsCallOnly))
        output_status_message("IsCallTrackingEnabled: {0}".format(extension.IsCallTrackingEnabled))
        output_status_message("PhoneNumber: {0}".format(extension.PhoneNumber))
        output_status_message("RequireTollFreeTrackingNumber: {0}".format(extension.RequireTollFreeTrackingNumber))
        output_status_message("Status: {0}".format(extension.Status))
        output_status_message("Version: {0}".format(extension.Version))
        output_status_message('')

def output_callout_ad_extension(extension):
    if extension is not None:
        output_status_message("Id: {0}".format(extension.Id))
        output_status_message("Type: {0}".format(extension.Type))
        output_status_message("Callout Text: {0}".format(extension.Text))
        output_status_message("Status: {0}".format(extension.Status))
        output_status_message("Version: {0}".format(extension.Version))
        output_status_message('')

def output_location_ad_extension(extension):
    if extension is not None:
        output_status_message("Id: {0}".format(extension.Id))
        output_status_message("Type: {0}".format(extension.Type))
        if extension.Address is not None:
            output_status_message("CityName: {0}".format(extension.Address.CityName))
            output_status_message("CountryCode: {0}".format(extension.Address.CountryCode))
            output_status_message("PostalCode: {0}".format(extension.Address.PostalCode))
            output_status_message("ProvinceCode: {0}".format(extension.Address.ProvinceCode))
            output_status_message("ProvinceName: {0}".format(extension.Address.ProvinceName))
            output_status_message("StreetAddress: {0}".format(extension.Address.StreetAddress))
            output_status_message("StreetAddress2: {0}".format(extension.Address.StreetAddress2))
        output_status_message("CompanyName: {0}".format(extension.CompanyName))
        output_status_message("GeoCodeStatus: {0}".format(extension.GeoCodeStatus))
        if extension.GeoPoint is not None:
            output_status_message("GeoPoint: ")
            output_status_message("LatitudeInMicroDegrees: {0}".format(extension.GeoPoint.LatitudeInMicroDegrees))
            output_status_message("LongitudeInMicroDegrees: {0}".format(extension.GeoPoint.LongitudeInMicroDegrees))
        output_status_message("IconMediaId: {0}".format(extension.IconMediaId))
        output_status_message("ImageMediaId: {0}".format(extension.ImageMediaId))
        output_status_message("PhoneNumber: {0}".format(extension.PhoneNumber))
        output_status_message("Status: {0}".format(extension.Status))
        output_status_message("Version: {0}".format(extension.Version))
        output_status_message('')

def output_review_ad_extension(extension):
    if extension is not None:
        output_status_message("Id: {0}".format(extension.Id))
        output_status_message("Type: {0}".format(extension.Type))
        output_status_message("IsExact: {0}".format(extension.IsExact))
        output_status_message("Source: {0}".format(extension.Source))
        output_status_message("Text: {0}".format(extension.Text))
        output_status_message("Url: {0}".format(extension.Url))
        output_status_message("Status: {0}".format(extension.Status))
        output_status_message("Version: {0}".format(extension.Version))
        output_status_message('')

def output_site_links_ad_extension(extension):
    if extension is not None:
        output_status_message("Id: {0}".format(extension.Id))
        output_status_message("Type: {0}".format(extension.Type))
        output_status_message("Status: {0}".format(extension.Status))
        output_status_message("Version: {0}".format(extension.Version))
        output_site_links(extension.SiteLinks['SiteLink'])
        output_status_message('')

def output_site_links(site_links):
    if site_links is not None:
        for site_link in site_links:
            output_status_message("Description1: {0}".format(site_link.Description1))
            output_status_message("Description2: {0}".format(site_link.Description2))
            output_status_message("DevicePreference: {0}".format(site_link.DevicePreference))
            output_status_message("DisplayText: {0}".format(site_link.DisplayText))
            output_status_message("DestinationUrl: {0}".format(site_link.DestinationUrl))
            output_status_message("FinalMobileUrls: ")
            if site_link.FinalMobileUrls is not None:
                for final_mobile_url in site_link.FinalMobileUrls['string']:
                    output_status_message("\t{0}".format(final_mobile_url))
            output_status_message("FinalUrls: ")
            if site_link.FinalUrls is not None:
                for final_url in site_link.FinalUrls['string']:
                    output_status_message("\t{0}".format(final_url))
            output_status_message("TrackingUrlTemplate: {0}".format(site_link.TrackingUrlTemplate))
            output_status_message("UrlCustomParameters: ")
            if site_link.UrlCustomParameters is not None and site_link.UrlCustomParameters.Parameters is not None:
                for custom_parameter in site_link.UrlCustomParameters.Parameters['CustomParameter']:
                    output_status_message("\tKey: {0}".format(custom_parameter.Key))
                    output_status_message("\tValue: {0}".format(custom_parameter.Value))
            output_status_message('')

def output_status_message(message):
    print(message)

def output_bulk_performance_data(performance_data):
    if performance_data is not None:
        output_status_message("AverageCostPerClick: {0}".format(performance_data.average_cost_per_click))
        output_status_message("AverageCostPerThousandImpressions: {0}".format(performance_data.average_cost_per_thousand_impressions))
        output_status_message("AveragePosition: {0}".format(performance_data.average_position))
        output_status_message("Clicks: {0}".format(performance_data.clicks))
        output_status_message("ClickThroughRate: {0}".format(performance_data.click_through_rate))
        output_status_message("Conversions: {0}".format(performance_data.conversions))
        output_status_message("CostPerConversion: {0}".format(performance_data.cost_per_conversion))
        output_status_message("Impressions: {0}".format(performance_data.impressions))
        output_status_message("Spend: {0}".format(performance_data.spend))

def output_bulk_quality_score_data(quality_score_data):
    if quality_score_data is not None:
        output_status_message("KeywordRelevance: {0}".format(quality_score_data.keyword_relevance))
        output_status_message("LandingPageRelevance: {0}".format(quality_score_data.landing_page_relevance))
        output_status_message("LandingPageUserExperience: {0}".format(quality_score_data._landing_page_user_experience))
        output_status_message("QualityScore: {0}".format(quality_score_data.quality_score))

def output_bulk_errors(errors):
    for error in errors:
        if error.error is not None:
            output_status_message("Number: {0}".format(error.error))
        output_status_message("Error: {0}".format(error.number))
        if error.editorial_reason_code is not None:
            output_status_message("EditorialTerm: {0}".format(error.editorial_term))
            output_status_message("EditorialReasonCode: {0}".format(error.editorial_reason_code))
            output_status_message("EditorialLocation: {0}".format(error.editorial_location))
            output_status_message("PublisherCountries: {0}".format(error.publisher_countries))
        output_status_message('')

def output_bing_ads_webfault_error(error):
    if hasattr(error, 'ErrorCode'):
        output_status_message("ErrorCode: {0}".format(error.ErrorCode))
    if hasattr(error, 'Code'):
        output_status_message("Code: {0}".format(error.Code))
    if hasattr(error, 'Message'):
        output_status_message("Message: {0}".format(error.Message))
    output_status_message('')

def output_webfault_errors(ex):
    if hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'ApiFault') \
        and hasattr(ex.fault.detail.ApiFault, 'OperationErrors') \
        and hasattr(ex.fault.detail.ApiFault.OperationErrors, 'OperationError'):
        api_errors=ex.fault.detail.ApiFault.OperationErrors.OperationError
        if type(api_errors) == list:
            for api_error in api_errors:
                output_bing_ads_webfault_error(api_error)
        else:
            output_bing_ads_webfault_error(api_errors)
    elif hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'AdApiFaultDetail') \
        and hasattr(ex.fault.detail.AdApiFaultDetail, 'Errors') \
        and hasattr(ex.fault.detail.AdApiFaultDetail.Errors, 'AdApiError'):
        api_errors=ex.fault.detail.AdApiFaultDetail.Errors.AdApiError
        if type(api_errors) == list:
            for api_error in api_errors:
                output_bing_ads_webfault_error(api_error)
        else:
            output_bing_ads_webfault_error(api_errors)
    elif hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'ApiFaultDetail') \
        and hasattr(ex.fault.detail.ApiFaultDetail, 'BatchErrors') \
        and hasattr(ex.fault.detail.ApiFaultDetail.BatchErrors, 'BatchError'):
        api_errors=ex.fault.detail.ApiFaultDetail.BatchErrors.BatchError
        if type(api_errors) == list:
            for api_error in api_errors:
                output_bing_ads_webfault_error(api_error)
        else:
            output_bing_ads_webfault_error(api_errors)
    elif hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'ApiFaultDetail') \
        and hasattr(ex.fault.detail.ApiFaultDetail, 'OperationErrors') \
        and hasattr(ex.fault.detail.ApiFaultDetail.OperationErrors, 'OperationError'):
        api_errors=ex.fault.detail.ApiFaultDetail.OperationErrors.OperationError
        if type(api_errors) == list:
            for api_error in api_errors:
                output_bing_ads_webfault_error(api_error)
        else:
            output_bing_ads_webfault_error(api_errors)
    elif hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'EditorialApiFaultDetail') \
        and hasattr(ex.fault.detail.EditorialApiFaultDetail, 'BatchErrors') \
        and hasattr(ex.fault.detail.EditorialApiFaultDetail.BatchErrors, 'BatchError'):
        api_errors=ex.fault.detail.EditorialApiFaultDetail.BatchErrors.BatchError
        if type(api_errors) == list:
            for api_error in api_errors:
                output_bing_ads_webfault_error(api_error)
        else:
            output_bing_ads_webfault_error(api_errors)
    elif hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'EditorialApiFaultDetail') \
        and hasattr(ex.fault.detail.EditorialApiFaultDetail, 'EditorialErrors') \
        and hasattr(ex.fault.detail.EditorialApiFaultDetail.EditorialErrors, 'EditorialError'):
        api_errors=ex.fault.detail.EditorialApiFaultDetail.EditorialErrors.EditorialError
        if type(api_errors) == list:
            for api_error in api_errors:
                output_bing_ads_webfault_error(api_error)
        else:
            output_bing_ads_webfault_error(api_errors)
    elif hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'EditorialApiFaultDetail') \
        and hasattr(ex.fault.detail.EditorialApiFaultDetail, 'OperationErrors') \
        and hasattr(ex.fault.detail.EditorialApiFaultDetail.OperationErrors, 'OperationError'):
        api_errors=ex.fault.detail.EditorialApiFaultDetail.OperationErrors.OperationError
        if type(api_errors) == list:
            for api_error in api_errors:
                output_bing_ads_webfault_error(api_error)
        else:
            output_bing_ads_webfault_error(api_errors)
    # Handle serialization errors e.g. The formatter threw an exception while trying to deserialize the message: 
    # There was an error while trying to deserialize parameter https://bingads.microsoft.com/CampaignManagement/v10:Entities.
    elif hasattr(ex.fault, 'detail') \
        and hasattr(ex.fault.detail, 'ExceptionDetail'):
        api_errors=ex.fault.detail.ExceptionDetail
        if type(api_errors) == list:
            for api_error in api_errors:
                output_status_message(api_error.Message)
        else:
            output_status_message(api_errors.Message)
    else:
        raise Exception('Unknown WebFault')

def set_elements_to_none(suds_object):
    # Bing Ads Campaign Management service operations require that if you specify a non-primitives, 
    # it must be one of the values defined by the service i.e. it cannot be a nil element. 
    # Since Suds requires non-primitives and Bing Ads won't accept nil elements in place of an enum value, 
    # you must either set the non-primitives or they must be set to None. Also in case new properties are added 
    # in a future service release, it is a good practice to set each element of the SUDS object to None as a baseline. 

    for (element) in suds_object:
        suds_object.__setitem__(element[0], None)
    return suds_object

def write_entities_and_upload_file(upload_entities):
    # Writes the specified entities to a local file and uploads the file. We could have uploaded directly
    # without writing to file. This example writes to file as an exercise so that you can view the structure 
    # of the bulk records being uploaded as needed. 
    writer=BulkFileWriter(FILE_DIRECTORY+UPLOAD_FILE_NAME);
    for entity in upload_entities:
        writer.write_entity(entity)
    writer.close()

    file_upload_parameters=FileUploadParameters(
        result_file_directory=FILE_DIRECTORY,
        compress_upload_file=True,
        result_file_name=RESULT_FILE_NAME,
        overwrite_result_file=True,
        upload_file_path=FILE_DIRECTORY+UPLOAD_FILE_NAME,
        response_mode='ErrorsAndResults'
    )

    bulk_file_path=bulk_service.upload_file(file_upload_parameters, progress=print_percent_complete)

    download_entities=[]
    entities_generator=read_entities_from_bulk_file(file_path=bulk_file_path, result_file_type=ResultFileType.upload, file_format=FILE_FORMAT)
    for entity in entities_generator:
        download_entities.append(entity)

    return download_entities

def read_entities_from_bulk_file(file_path, result_file_type, file_format):
    with BulkFileReader(file_path=file_path, result_file_type=result_file_type, file_format=file_format) as reader:
        for entity in reader:
            yield entity


# Main execution
if __name__ == '__main__':

    errors=[]

    try:
        # You should authenticate for Bing Ads production services with a Microsoft Account, 
        # instead of providing the Bing Ads username and password set. 
        # Authentication with a Microsoft Account is currently not supported in Sandbox.
        authenticate_with_oauth()

        # Uncomment to run with Bing Ads legacy UserName and Password credentials.
        # For example you would use this method to authenticate in sandbox.
        #authenticate_with_username()
        
        # Set to an empty user identifier to get the current authenticated Bing Ads user,
        # and then search for all accounts the user may access.
        user=customer_service.GetUser(None).User
        accounts=search_accounts_by_user_id(user.Id)

        # For this example we'll use the first account.
        authorization_data.account_id=accounts['Account'][0].Id
        authorization_data.customer_id=accounts['Account'][0].ParentCustomerId

        # Prepare the bulk entities that you want to upload. Each bulk entity contains the corresponding campaign management object,  
        # and additional elements needed to read from and write to a bulk file.

        bulk_campaign=BulkCampaign()
    
        # The client_id may be used to associate records in the bulk upload file with records in the results file. The value of this field  
        # is not used or stored by the server; it is simply copied from the uploaded record to the corresponding result record. 
        # Note: This bulk file Client Id is not related to an application Client Id for OAuth. 

        bulk_campaign.client_id='YourClientIdGoesHere'
        campaign=set_elements_to_none(campaign_service.factory.create('Campaign'))
    
        # When using the Campaign Management service, the Id cannot be set. In the context of a BulkCampaign, the Id is optional  
        # and may be used as a negative reference key during bulk upload. For example the same negative reference key for the campaign Id  
        # will be used when associating ad extensions with the campaign. 

        campaign.Id=CAMPAIGN_ID_KEY
        campaign.Name="Summer Shoes " + strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        campaign.Description="Summer shoes line."
        campaign.BudgetType='MonthlyBudgetSpendUntilDepleted'
        campaign.MonthlyBudget=1000
        campaign.TimeZone='PacificTimeUSCanadaTijuana'
        campaign.Status='Paused'

        # DaylightSaving is not supported in the Bulk file schema. Whether or not you specify it in a BulkCampaign,
        # the value is not written to the Bulk file, and by default DaylightSaving is set to true.
        campaign.DaylightSaving='True'

        # Used with FinalUrls shown in the sitelinks that we will add below.
        campaign.TrackingUrlTemplate="http://tracker.example.com/?season={_season}&promocode={_promocode}&u={lpurl}"

        bulk_campaign.campaign=campaign

        bulk_app_ad_extension=BulkAppAdExtension()
        bulk_app_ad_extension.account_id=authorization_data.account_id
        app_ad_extension=set_elements_to_none(campaign_service.factory.create('AppAdExtension'))
        app_ad_extension.Id=APP_AD_EXTENSION_ID_KEY
        app_ad_extension.AppPlatform='Windows'
        app_ad_extension.AppStoreId='AppStoreIdGoesHere'
        app_ad_extension.DisplayText='Contoso'
        app_ad_extension.DestinationUrl='DestinationUrlGoesHere'
        app_ad_extension.Status=None
        bulk_app_ad_extension.app_ad_extension=app_ad_extension

        bulk_campaign_app_ad_extension=BulkCampaignAppAdExtension()
        app_ad_extension_id_to_entity_id_association=campaign_service.factory.create('AdExtensionIdToEntityIdAssociation')
        app_ad_extension_id_to_entity_id_association.AdExtensionId=APP_AD_EXTENSION_ID_KEY
        app_ad_extension_id_to_entity_id_association.EntityId=CAMPAIGN_ID_KEY
        bulk_campaign_app_ad_extension.ad_extension_id_to_entity_id_association=app_ad_extension_id_to_entity_id_association

        bulk_call_ad_extension=BulkCallAdExtension()
        bulk_call_ad_extension.account_id=authorization_data.account_id
        call_ad_extension=set_elements_to_none(campaign_service.factory.create('CallAdExtension'))
        call_ad_extension.CountryCode="US"
        call_ad_extension.PhoneNumber="2065550100"
        call_ad_extension.IsCallOnly=False
        call_ad_extension.Status=None
        call_ad_extension.Id=CALL_AD_EXTENSION_ID_KEY
        bulk_call_ad_extension.call_ad_extension=call_ad_extension

        bulk_campaign_call_ad_extension=BulkCampaignCallAdExtension()
        call_ad_extension_id_to_entity_id_association=campaign_service.factory.create('AdExtensionIdToEntityIdAssociation')
        call_ad_extension_id_to_entity_id_association.AdExtensionId=CALL_AD_EXTENSION_ID_KEY
        call_ad_extension_id_to_entity_id_association.EntityId=CAMPAIGN_ID_KEY
        bulk_campaign_call_ad_extension.ad_extension_id_to_entity_id_association=call_ad_extension_id_to_entity_id_association

        bulk_callout_ad_extension=BulkCalloutAdExtension()
        bulk_callout_ad_extension.account_id=authorization_data.account_id
        callout_ad_extension=set_elements_to_none(campaign_service.factory.create('CalloutAdExtension'))
        callout_ad_extension.Text="Callout Text"
        callout_ad_extension.Status=None
        callout_ad_extension.Id=CALLOUT_AD_EXTENSION_ID_KEY
        bulk_callout_ad_extension.callout_ad_extension=callout_ad_extension

        bulk_campaign_callout_ad_extension=BulkCampaignCalloutAdExtension()
        callout_ad_extension_id_to_entity_id_association=campaign_service.factory.create('AdExtensionIdToEntityIdAssociation')
        callout_ad_extension_id_to_entity_id_association.AdExtensionId=CALLOUT_AD_EXTENSION_ID_KEY
        callout_ad_extension_id_to_entity_id_association.EntityId=CAMPAIGN_ID_KEY
        bulk_campaign_callout_ad_extension.ad_extension_id_to_entity_id_association=callout_ad_extension_id_to_entity_id_association

        bulk_location_ad_extension=BulkLocationAdExtension()
        bulk_location_ad_extension.account_id=authorization_data.account_id
        location_ad_extension=set_elements_to_none(campaign_service.factory.create('LocationAdExtension'))
        location_ad_extension.PhoneNumber="206-555-0100"
        location_ad_extension.CompanyName="Contoso Shoes"
        location_ad_extension.IconMediaId=None
        location_ad_extension.ImageMediaId=None
        location_ad_extension.Status=None
        location_ad_extension.GeoCodeStatus=None
        location_ad_extension.GeoPoint=None
        address=campaign_service.factory.create('Address')
        address.StreetAddress="1234 Washington Place"
        address.StreetAddress2="Suite 1210"
        address.CityName="Woodinville"
        address.ProvinceName="WA"
        address.CountryCode="US"
        address.PostalCode="98608"
        location_ad_extension.Address=address
        location_ad_extension.Id=LOCATION_AD_EXTENSION_ID_KEY
        bulk_location_ad_extension.location_ad_extension=location_ad_extension

        bulk_campaign_location_ad_extension=BulkCampaignLocationAdExtension()
        location_ad_extension_id_to_entity_id_association=campaign_service.factory.create('AdExtensionIdToEntityIdAssociation')
        location_ad_extension_id_to_entity_id_association.AdExtensionId=LOCATION_AD_EXTENSION_ID_KEY
        location_ad_extension_id_to_entity_id_association.EntityId=CAMPAIGN_ID_KEY
        bulk_campaign_location_ad_extension.ad_extension_id_to_entity_id_association=location_ad_extension_id_to_entity_id_association

        bulk_review_ad_extension=BulkReviewAdExtension()
        bulk_review_ad_extension.account_id=authorization_data.account_id
        review_ad_extension=set_elements_to_none(campaign_service.factory.create('ReviewAdExtension'))
        review_ad_extension.IsExact=True
        review_ad_extension.Source="Review Source Name"
        review_ad_extension.Text="Review Text"
        review_ad_extension.Url="http://review.contoso.com" # The Url of the third-party review. This is not your business Url.
        review_ad_extension.Status=None
        review_ad_extension.Id=REVIEW_AD_EXTENSION_ID_KEY
        bulk_review_ad_extension.review_ad_extension=review_ad_extension

        bulk_campaign_review_ad_extension=BulkCampaignReviewAdExtension()
        review_ad_extension_id_to_entity_id_association=campaign_service.factory.create('AdExtensionIdToEntityIdAssociation')
        review_ad_extension_id_to_entity_id_association.AdExtensionId=REVIEW_AD_EXTENSION_ID_KEY
        review_ad_extension_id_to_entity_id_association.EntityId=CAMPAIGN_ID_KEY
        bulk_campaign_review_ad_extension.ad_extension_id_to_entity_id_association=review_ad_extension_id_to_entity_id_association

        bulk_site_link_ad_extension=BulkSiteLinkAdExtension()
        bulk_site_link_ad_extension.account_id=authorization_data.account_id
        site_links_ad_extension=set_elements_to_none(campaign_service.factory.create('SiteLinksAdExtension'))
        site_links=campaign_service.factory.create('ArrayOfSiteLink')

        for index in range(2):
            site_link=set_elements_to_none(campaign_service.factory.create('SiteLink'))
            site_link.DisplayText = "Women's Shoe Sale " + str(index+1)

            # If you are currently using the Destination URL, you must upgrade to Final URLs. 
            # Here is an example of a DestinationUrl you might have used previously. 
            # site_link.DestinationUrl='http://www.contoso.com/womenshoesale/?season=spring&promocode=PROMO123'

            # To migrate from DestinationUrl to FinalUrls for existing sitelinks, you can set DestinationUrl
            # to an empty string when updating the sitelink. If you are removing DestinationUrl,
            # then FinalUrls is required.
            # site_link.DestinationUrl=""
            
            # With FinalUrls you can separate the tracking template, custom parameters, and 
            # landing page URLs.
            final_urls=campaign_service.factory.create('ns4:ArrayOfstring')
            final_urls.string.append('http://www.contoso.com/womenshoesale')
            site_link.FinalUrls=final_urls

            # Final Mobile URLs can also be used if you want to direct the user to a different page 
            # for mobile devices.
            final_mobile_urls=campaign_service.factory.create('ns4:ArrayOfstring')
            final_mobile_urls.string.append('http://mobile.contoso.com/womenshoesale')
            site_link.FinalMobileUrls=final_mobile_urls

            # You could use a tracking template which would override the campaign level
            # tracking template. Tracking templates defined for lower level entities 
            # override those set for higher level entities.
            # In this example we are using the campaign level tracking template.
            site_link.TrackingUrlTemplate=None

            # Set custom parameters that are specific to this sitelink, 
            # and can be used by the sitelink, ad group, campaign, or account level tracking template. 
            # In this example we are using the campaign level tracking template.
            url_custom_parameters=campaign_service.factory.create('ns0:CustomParameters')
            parameters=campaign_service.factory.create('ns0:ArrayOfCustomParameter')
            custom_parameter1=campaign_service.factory.create('ns0:CustomParameter')
            custom_parameter1.Key='promoCode'
            custom_parameter1.Value='PROMO' + str(index+1)
            parameters.CustomParameter.append(custom_parameter1)
            custom_parameter2=campaign_service.factory.create('ns0:CustomParameter')
            custom_parameter2.Key='season'
            custom_parameter2.Value='summer'
            parameters.CustomParameter.append(custom_parameter2)
            url_custom_parameters.Parameters=parameters
            site_link.UrlCustomParameters=url_custom_parameters
            site_links.SiteLink.append(site_link)

        site_links_ad_extension.SiteLinks=site_links
        site_links_ad_extension.Status=None
        site_links_ad_extension.Id=SITE_LINK_AD_EXTENSION_ID_KEY
        bulk_site_link_ad_extension.site_links_ad_extension=site_links_ad_extension

        bulk_campaign_site_link_ad_extension=BulkCampaignSiteLinkAdExtension()
        site_link_ad_extension_id_to_entity_id_association=campaign_service.factory.create('AdExtensionIdToEntityIdAssociation')
        site_link_ad_extension_id_to_entity_id_association.AdExtensionId=SITE_LINK_AD_EXTENSION_ID_KEY
        site_link_ad_extension_id_to_entity_id_association.EntityId=CAMPAIGN_ID_KEY
        bulk_campaign_site_link_ad_extension.ad_extension_id_to_entity_id_association=site_link_ad_extension_id_to_entity_id_association
        
        # Upload the entities created above. 
        # Dependent entities such as BulkCampaignCallAdExtension must be written after any dependencies,  
        # for example the BulkCampaign and BulkCallAdExtension. 

        upload_entities=[]
        upload_entities.append(bulk_campaign)
        upload_entities.append(bulk_app_ad_extension)
        upload_entities.append(bulk_campaign_app_ad_extension)
        upload_entities.append(bulk_call_ad_extension)
        upload_entities.append(bulk_campaign_call_ad_extension)
        upload_entities.append(bulk_callout_ad_extension)
        upload_entities.append(bulk_campaign_callout_ad_extension)
        upload_entities.append(bulk_location_ad_extension)
        upload_entities.append(bulk_campaign_location_ad_extension)
        upload_entities.append(bulk_review_ad_extension)
        upload_entities.append(bulk_campaign_review_ad_extension)
        upload_entities.append(bulk_site_link_ad_extension)
        upload_entities.append(bulk_campaign_site_link_ad_extension)
        
        output_status_message("\nAdding campaign, ad extensions, and associations . . .")
        download_entities=write_entities_and_upload_file(upload_entities)

        campaign_results=[]
        app_ad_extension_results=[]
        call_ad_extension_results=[]
        callout_ad_extension_results=[]
        location_ad_extension_results=[]
        review_ad_extension_results=[]
        site_link_ad_extension_results=[]

        for entity in download_entities:
            if isinstance(entity, BulkCampaign):
                campaign_results.append(entity)
                output_bulk_campaigns([entity])
            if isinstance(entity, BulkAppAdExtension):
                app_ad_extension_results.append(entity)
                output_bulk_app_ad_extensions([entity])
            if isinstance(entity, BulkCampaignAppAdExtension):
                output_bulk_campaign_app_ad_extensions([entity])
            if isinstance(entity, BulkCallAdExtension):
                call_ad_extension_results.append(entity)
                output_bulk_call_ad_extensions([entity])
            if isinstance(entity, BulkCampaignCallAdExtension):
                output_bulk_campaign_call_ad_extensions([entity])
            if isinstance(entity, BulkCalloutAdExtension):
                callout_ad_extension_results.append(entity)
                output_bulk_callout_ad_extensions([entity])
            if isinstance(entity, BulkCampaignCalloutAdExtension):
                output_bulk_campaign_callout_ad_extensions([entity])
            if isinstance(entity, BulkLocationAdExtension):
                location_ad_extension_results.append(entity)
                output_bulk_location_ad_extensions([entity])
            if isinstance(entity, BulkCampaignLocationAdExtension):
                output_bulk_campaign_location_ad_extensions([entity])
            if isinstance(entity, BulkReviewAdExtension):
                review_ad_extension_results.append(entity)
                output_bulk_review_ad_extensions([entity])
            if isinstance(entity, BulkCampaignReviewAdExtension):
                output_bulk_campaign_review_ad_extensions([entity])
            if isinstance(entity, BulkSiteLinkAdExtension):
                site_link_ad_extension_results.append(entity)
                output_bulk_site_link_ad_extensions([entity])
            if isinstance(entity, BulkCampaignSiteLinkAdExtension):
                output_bulk_campaign_site_link_ad_extensions([entity])
            
              
        #Update the site links ad extension. 
        #Add an additional site link, and update an existing site link.

        #Do not create a BulkSiteLinkAdExtension for update, unless you want to replace all existing SiteLinks
        #with the specified SiteLinks for the specified ad extension. 
        #Instead you should upload one or more site links as a list of BulkSiteLink.

        upload_entities=[]
        
        bulk_site_link=BulkSiteLink()
        site_link=set_elements_to_none(campaign_service.factory.create('SiteLink'))
        site_link.DisplayText = "Women's Shoe Sale 3"
        site_link.Order=3

        # If you are currently using the Destination URL, you must upgrade to Final URLs. 
        # Here is an example of a DestinationUrl you might have used previously. 
        #site_link.DestinationUrl='http://www.contoso.com/womenshoesale/?season=spring&promocode=PROMO123'
            
        # With FinalUrls you can separate the tracking template, custom parameters, and 
        # landing page URLs.
        final_urls=campaign_service.factory.create('ns4:ArrayOfstring')
        final_urls.string.append('http://www.contoso.com/womenshoesale')
        site_link.FinalUrls=final_urls

        # Final Mobile URLs can also be used if you want to direct the user to a different page 
        # for mobile devices.
        final_mobile_urls=campaign_service.factory.create('ns4:ArrayOfstring')
        final_mobile_urls.string.append('http://mobile.contoso.com/womenshoesale')
        site_link.FinalMobileUrls=final_mobile_urls

        # You could use a tracking template which would override the campaign level
        # tracking template. Tracking templates defined for lower level entities 
        # override those set for higher level entities.
        # In this example we are using the campaign level tracking template.
        site_link.TrackingUrlTemplate=None

        # Set custom parameters that are specific to this ad, 
        # and can be used by the ad, ad group, campaign, or account level tracking template. 
        # In this example we are using the campaign level tracking template.
        url_custom_parameters=campaign_service.factory.create('ns0:CustomParameters')
        parameters=campaign_service.factory.create('ns0:ArrayOfCustomParameter')
        custom_parameter1=campaign_service.factory.create('ns0:CustomParameter')
        custom_parameter1.Key='promoCode'
        custom_parameter1.Value='PROMO3'
        parameters.CustomParameter.append(custom_parameter1)
        custom_parameter2=campaign_service.factory.create('ns0:CustomParameter')
        custom_parameter2.Key='season'
        custom_parameter2.Value='summer'
        parameters.CustomParameter.append(custom_parameter2)
        url_custom_parameters.Parameters=parameters
        site_link.UrlCustomParameters=url_custom_parameters
        bulk_site_link.site_link=site_link
        
        if site_link_ad_extension_results.count > 0:
            existing_site_link=site_link_ad_extension_results[0].site_links[0]

            # To remove a subset of custom parameters, specify the custom parameters that 
            # you want to keep in the Parameters element of the CustomParameters object.
            updated_url_custom_parameters=campaign_service.factory.create('ns0:CustomParameters')
            updated_parameters=campaign_service.factory.create('ns0:ArrayOfCustomParameter')
            updated_custom_parameter=campaign_service.factory.create('ns0:CustomParameter')
            updated_custom_parameter.Key='promoCode'
            updated_custom_parameter.Value='updatedpromo'
            updated_parameters.CustomParameter.append(updated_custom_parameter)
            updated_url_custom_parameters.Parameters=updated_parameters
            existing_site_link.site_link.UrlCustomParameters=updated_url_custom_parameters
            upload_entities.append(existing_site_link)

            # Associate the new site link with the identifier of the existing site links ad extension
            bulk_site_link.ad_extension_id=existing_site_link.ad_extension_id
            bulk_site_link.account_id=authorization_data.account_id
            upload_entities.append(bulk_site_link)

        # Upload and write the output

        output_status_message("\nUpdating sitelinks . . .")
        download_entities=write_entities_and_upload_file(upload_entities)
        
        for entity in download_entities:
            if isinstance(entity, BulkSiteLink):
                output_bulk_site_links([entity])

        # Delete the campaign and ad extensions that were previously added. 
        # You should remove this region if you want to view the added entities in the 
        # Bing Ads web application or another tool.

        # You must set the Id field to the corresponding entity identifier, and the Status field to Deleted. 

        # When you delete a BulkCampaign or BulkCallAdExtension, dependent entities such as BulkCampaignCallAdExtension 
        # are deleted without being specified explicitly.  

        upload_entities=[]

        for campaign_result in campaign_results:
            campaign_result.campaign.Status='Deleted'
            upload_entities.append(campaign_result)
        
        for app_ad_extension_result in app_ad_extension_results:
            app_ad_extension_result.app_ad_extension.Status='Deleted'
            # By default the sample does not successfully create any app ad extensions,
            # because you need to provide details such as the AppStoreId.
            # You can uncomment the following line if you added an app ad extension above.
            # upload_entities.append(app_ad_extension_result)

        for call_ad_extension_result in call_ad_extension_results:
            call_ad_extension_result.call_ad_extension.Status='Deleted'
            upload_entities.append(call_ad_extension_result)

        for callout_ad_extension_result in callout_ad_extension_results:
            callout_ad_extension_result.callout_ad_extension.Status='Deleted'
            upload_entities.append(callout_ad_extension_result)

        for location_ad_extension_result in location_ad_extension_results:
            location_ad_extension_result.location_ad_extension.Status='Deleted'
            upload_entities.append(location_ad_extension_result)

        for review_ad_extension_result in review_ad_extension_results:
            review_ad_extension_result.review_ad_extension.Status='Deleted'
            upload_entities.append(review_ad_extension_result)

        for site_link_ad_extension_result in site_link_ad_extension_results:
            site_link_ad_extension_result.site_links_ad_extension.Status='Deleted'
            upload_entities.append(site_link_ad_extension_result)

        output_status_message("\nDeleting campaign and ad extensions . . .")
        download_entities=write_entities_and_upload_file(upload_entities)

        for entity in download_entities:
            if isinstance(entity, BulkCampaign):
                output_bulk_campaigns([entity])
            if isinstance(entity, BulkAppAdExtension):
                output_bulk_app_ad_extensions([entity])
            if isinstance(entity, BulkCallAdExtension):
                output_bulk_call_ad_extensions([entity])
            if isinstance(entity, BulkCalloutAdExtension):
                output_bulk_callout_ad_extensions([entity])
            if isinstance(entity, BulkLocationAdExtension):
                output_bulk_location_ad_extensions([entity])
            if isinstance(entity, BulkReviewAdExtension):
                output_bulk_review_ad_extensions([entity])
            if isinstance(entity, BulkSiteLinkAdExtension):
                output_bulk_site_link_ad_extensions([entity])
            
        output_status_message("Program execution completed")

    except WebFault as ex:
        output_webfault_errors(ex)
    except Exception as ex:
        output_status_message(ex)

