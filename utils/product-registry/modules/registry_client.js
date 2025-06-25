// This module provides functions to interact with the BC Gov Product Registry API.

const ProductTypes = Object.freeze({
	PUBLIC:   Symbol("public"),
	PRIVATE:  Symbol("private"),
});

async function getToken(client_id, client_secret) {
	const tokenResponse = await fetch('https://loginproxy.gov.bc.ca/auth/realms/platform-services/protocol/openid-connect/token', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded',
		},
		body: new URLSearchParams({
			grant_type: 'client_credentials',
			client_id: client_id,
			client_secret: client_secret,
		}),
	});

	const {access_token} = await tokenResponse.json();
	return access_token;
}

async function doRegistryGetAPICall(access_token, path) {
	const dataResponse = await fetch(path, {
		method: 'GET',
		headers: {
			'Authorization': `Bearer ${access_token}`,
			'Content-Type': 'application/json',
		},
	});

	return await dataResponse.json();
}

async function getProduct(access_token, product_type, product_id) {

	return await doRegistryGetAPICall(access_token, `https://registry.developer.gov.bc.ca/api/v1/${product_type.description}-cloud/products/${product_id}`);
}

async function getProducts(access_token, product_type) {
	return await doRegistryGetAPICall(access_token, `https://registry.developer.gov.bc.ca/api/v1/${product_type.description}-cloud/products`);
}

export{getToken, getProducts, getProduct, ProductTypes};
