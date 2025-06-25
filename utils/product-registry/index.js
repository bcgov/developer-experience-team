import {getToken,getProducts,getProduct, ProductTypes} from "./modules/registry_client.js";

const client_id = 'blah';
const client_secret = 'blah';
const token = await getToken(client_id,client_secret);

const data = await getProducts(token, ProductTypes.PUBLIC);
console.log(JSON.stringify(data));



