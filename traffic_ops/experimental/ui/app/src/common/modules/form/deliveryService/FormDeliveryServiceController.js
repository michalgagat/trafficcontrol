var FormDeliveryServiceController = function(deliveryService, $scope, $uibModal, $anchorScroll, formUtils, locationUtils, cdnService, deliveryServiceService, profileService, typeService) {

    var deleteDeliveryService = function(ds) {
        deliveryServiceService.deleteDeliveryService(ds.id)
            .then(function() {
                locationUtils.navigateToPath('/configure/delivery-services');
            });
    };

    var getTypes = function() {
        typeService.getTypes()
            .then(function(result) {
                $scope.types = result;
            });
    };

    var getCDNs = function() {
        cdnService.getCDNs()
            .then(function(result) {
                $scope.cdns = result;
            });
    };

    var getProfiles = function() {
        profileService.getProfiles()
            .then(function(result) {
                $scope.profiles = result;
            });
    };

    $scope.deliveryServiceCopy = angular.copy(deliveryService);

    $scope.deliveryService = deliveryService;

    $scope.props = [
        { name: 'id', required: true, readonly: true },
        { name: 'displayName', required: true, maxLength: 48 },
        { name: 'xmlId', required: true, maxLength: 48 },
        { name: 'active', required: true, maxLength: 1 },
        { name: 'signed', required: true, maxLength: 1 },
        { name: 'qstringIgnore', required: true, maxLength: 1 },
        { name: 'geoLimit', required: true, maxLength: 1 },
        { name: 'httpBypassFqdn', required: false, maxLength: 255 },
        { name: 'dnsBypassIp', required: false, maxLength: 45 },
        { name: 'dnsBypassIp6', required: false, maxLength: 45 },
        { name: 'dnsBypassTtl', required: false, maxLength: 11 },
        { name: 'orgServerFqdn', required: false, maxLength: 255 },
        { name: 'ccrDnsTtl', required: false, maxLength: 11 },
        { name: 'globalMaxMbps', required: false, maxLength: 11 },
        { name: 'globalMaxTps', required: false, maxLength: 11 },
        { name: 'longDesc', required: false, maxLength: 1024 },
        { name: 'longDesc1', required: false, maxLength: 1024 },
        { name: 'longDesc2', required: false, maxLength: 1024 },
        { name: 'maxDnsAnswers', required: false, maxLength: 11 },
        { name: 'infoUrl', required: false, maxLength: 255 },
        { name: 'missLat', required: false, maxLength: 255, pattern: new RegExp('^[-+]?[0-9]*\.?[0-9]+$'), invalidMsg: 'Invalid coordinate' },
        { name: 'missLong', required: false, maxLength: 255, pattern: new RegExp('^[-+]?[0-9]*\.?[0-9]+$'), invalidMsg: 'Invalid coordinate' },
        { name: 'checkPath', required: false, maxLength: 255 },
        { name: 'protocol', required: false, maxLength: 4 },
        { name: 'sslKeyVersion', required: false, maxLength: 11 },
        { name: 'ipv6RoutingEnabled', required: false, maxLength: 4 },
        { name: 'rangeRequestHandling', required: false, maxLength: 4 },
        { name: 'edgeHeaderRewrite', required: false, maxLength: 2048 },
        { name: 'midHeaderRewrite', required: false, maxLength: 2048 },
        { name: 'originShield', required: false, maxLength: 1024 },
        { name: 'regexRemap', required: false, maxLength: 1024 },
        { name: 'remapText', required: false, maxLength: 2048 },
        { name: 'cacheurl', required: false, maxLength: 1024 },
        { name: 'multiSiteOrigin', required: false, maxLength: 1 },
        { name: 'trResponseHeaders', required: false, maxLength: 1024 },
        { name: 'initialDispersion', required: false, maxLength: 11 },
        { name: 'dnsBypassCname', required: false, maxLength: 255 },
        { name: 'trRequestHeaders', required: false, maxLength: 1024 }
    ];

    $scope.update = function(deliveryService) {
        deliveryServiceService.updateDeliveryService(deliveryService).
            then(function() {
                $scope.deliveryServiceCopy = angular.copy(deliveryService);
                $anchorScroll(); // scrolls window to top
            });
    };

    $scope.confirmDelete = function(ds) {
        var params = {
            title: 'Confirm Delete',
            message: 'This action CANNOT be undone. This will permanently delete ' + ds.displayName + '. Are you sure you want to delete ' + ds.displayName + '?'
        };
        var modalInstance = $uibModal.open({
            templateUrl: 'common/modules/dialog/confirm/dialog.confirm.tpl.html',
            controller: 'DialogConfirmController',
            size: 'md',
            resolve: {
                params: function () {
                    return params;
                }
            }
        });
        modalInstance.result.then(function() {
            deleteDeliveryService(ds);
        }, function () {
            // do nothing
        });
    };

    $scope.navigateToPath = locationUtils.navigateToPath;

    $scope.hasError = formUtils.hasError;

    $scope.hasPropertyError = formUtils.hasPropertyError;

    var init = function () {
        getTypes();
        getCDNs();
        getProfiles();
    };
    init();

};

FormDeliveryServiceController.$inject = ['deliveryService', '$scope', '$uibModal', '$anchorScroll', 'formUtils', 'locationUtils', 'cdnService', 'deliveryServiceService', 'profileService', 'typeService'];
module.exports = FormDeliveryServiceController;