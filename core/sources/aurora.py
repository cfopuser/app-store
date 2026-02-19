import requests

try:
    from gpapi import googleplay as gp
except Exception:  # pragma: no cover - dependency error handled at runtime.
    gp = None


class AuroraSource:
    def __init__(
        self,
        timeout: int = 30,
        locale: str = "en_US",
        timezone: str = "UTC",
        device_codename: str = "bacon",
        dispenser_url: str = "https://auroraoss.com/api/auth",
        dispenser_user_agent: str = "com.aurora.store-4.8.1-73",
    ):
        if gp is None:
            raise RuntimeError(
                "Aurora source requires 'matlink-gpapi' and a compatible protobuf version."
            )

        self.timeout = timeout
        self.dispenser_url = dispenser_url.rstrip("/")
        self.dispenser_user_agent = dispenser_user_agent
        self.api = gp.GooglePlayAPI(
            locale=locale,
            timezone=timezone,
            device_codename=device_codename,
        )

        # Downloader expects these two attributes.
        self.scraper = requests.Session()
        self.headers = {"User-Agent": dispenser_user_agent}

        self._authenticated = False
        self._version_code_by_package: dict[str, int] = {}

    def _get_dispenser_credentials(self) -> tuple[str, str]:
        response = requests.get(
            self.dispenser_url,
            headers={"User-Agent": self.dispenser_user_agent},
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        email = payload.get("email")
        auth_token = payload.get("auth") or payload.get("authToken")

        if not email or not auth_token:
            raise RuntimeError("Aurora dispenser did not return valid credentials.")

        return email, auth_token

    def _authenticate(self):
        email, auth_token = self._get_dispenser_credentials()
        gsf_id = self.api.checkin(email, auth_token)
        self.api.login(authSubToken=auth_token, gsfId=gsf_id)
        self.api.toc()
        self.api.uploadDeviceConfig()
        self._authenticated = True

    def _run_with_auth(self, operation):
        last_error = None
        for attempt in range(2):
            try:
                if attempt == 1:
                    self._authenticated = False
                if not self._authenticated:
                    self._authenticate()
                return operation()
            except Exception as e:
                last_error = e
        raise RuntimeError(f"Aurora request failed: {last_error}") from last_error

    def _get_details(self, package_name: str) -> dict:
        def operation():
            details = self.api.details(package_name)
            if not isinstance(details, dict):
                raise RuntimeError("Unexpected details response from Aurora API.")
            return details

        return self._run_with_auth(operation)

    def get_latest_version(self, package_name: str):
        print(f"[*] [Aurora] Fetching metadata for: {package_name}")
        details = self._get_details(package_name)

        app_details = details.get("details", {}).get("appDetails", {})
        version_code = app_details.get("versionCode")
        version_string = app_details.get("versionString")
        title = details.get("title", package_name)

        if not version_code:
            return None, None, None

        self._version_code_by_package[package_name] = int(version_code)
        version = str(version_string) if version_string else str(version_code)
        # release_url is just the package name for this source.
        return version, package_name, title

    def _resolve_delivery(self, package_name: str, version_code: int) -> str:
        headers = self.api.getHeaders()
        params = {
            "ot": "1",
            "doc": package_name,
            "vc": str(version_code),
        }

        purchase_resp = requests.post(
            gp.PURCHASE_URL,
            headers=headers,
            params=params,
            timeout=self.timeout,
        )
        purchase_resp.raise_for_status()
        purchase_wrapper = gp.googleplay_pb2.ResponseWrapper.FromString(purchase_resp.content)
        if purchase_wrapper.commands.displayErrorMessage:
            raise RuntimeError(purchase_wrapper.commands.displayErrorMessage)

        buy_response = purchase_wrapper.payload.buyResponse
        if (
            buy_response.HasField("purchaseStatusResponse")
            and buy_response.purchaseStatusResponse.HasField("appDeliveryData")
            and buy_response.purchaseStatusResponse.appDeliveryData.downloadUrl
        ):
            return buy_response.purchaseStatusResponse.appDeliveryData.downloadUrl

        delivery_token = buy_response.downloadToken
        if not delivery_token:
            raise RuntimeError("Aurora purchase response did not include a delivery token.")

        delivery_resp = requests.get(
            gp.DELIVERY_URL,
            headers=headers,
            params={**params, "dtok": delivery_token},
            timeout=self.timeout,
        )
        delivery_resp.raise_for_status()
        delivery_wrapper = gp.googleplay_pb2.ResponseWrapper.FromString(delivery_resp.content)

        if delivery_wrapper.commands.displayErrorMessage:
            raise RuntimeError(delivery_wrapper.commands.displayErrorMessage)

        if not delivery_wrapper.payload.HasField("deliveryResponse"):
            raise RuntimeError("Aurora delivery response did not include payload.")

        app_delivery_data = delivery_wrapper.payload.deliveryResponse.appDeliveryData
        if not app_delivery_data.downloadUrl:
            raise RuntimeError("Aurora delivery response did not include download URL.")

        return app_delivery_data.downloadUrl

    def get_download_url(self, package_name: str):
        version_code = self._version_code_by_package.get(package_name)
        if version_code is None:
            details = self._get_details(package_name)
            app_details = details.get("details", {}).get("appDetails", {})
            version_code = int(app_details.get("versionCode", 0))

        if not version_code:
            raise RuntimeError("Could not resolve version code for Aurora download.")

        print(f"[*] [Aurora] Resolving delivery URL for {package_name} ({version_code})")

        download_url = self._run_with_auth(
            lambda: self._resolve_delivery(package_name, version_code)
        )

        # Keep download headers lightweight; final URL is tokenized.
        self.headers = {"User-Agent": self.dispenser_user_agent}
        return download_url
