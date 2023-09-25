---
title: Emergency Management BC - Evacuee Registration and Assistance (ERA)

slug: emergency-management

audience: developer

author: Fred Flintstone

content_owner: Wilma Flintstone

sort_order: 5
---
# Emergency Management BC - Evacuee Registration and Assistance (ERA)

A system to manage evacuees registrations and support provisioning for residents of the province of British Columbia

[![Lifecycle:Stable](https://img.shields.io/badge/Lifecycle-Stable-97ca00)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)

[![CodeQL](https://github.com/bcgov/embc-ess-mod/actions/workflows/codeql-analysis.yml/badge.svg?branch=master)](https://github.com/bcgov/embc-ess-mod/actions/workflows/codeql-analysis.yml)

[![OWASP Zap scan](https://github.com/bcgov/embc-ess-mod/actions/workflows/owasp_zap_scan.yml/badge.svg)](https://github.com/bcgov/embc-ess-mod/actions/workflows/owasp_zap_scan.yml)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Getting Help or Reporting an Issue

To report bugs/issues/feature requests, please email us at essmodernization@gov.bc.ca

## How to Contribute

If you would like to contribute, please see our [Contributing](./CONTRIBUTING.md) guidelines.

Please note that this project is released with a [Contributor Code of Conduct](./CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Architecture

```mermaid
graph LR;

   classDef openshift_era fill:#1C6758,stroke:#333,stroke-width:4px;
   classDef openshift_util fill:#607EAA,stroke:#333,stroke-width:4px;
   classDef bcgov fill:#839AA8,stroke:#333,stroke-width:4px,color:#000;

   Responders([Responders])
   Suppliers([Suppliers])
   Registrants([Registrants])
   ESS(ESS Backend)
   SSO(BCeID SSO)
   OAuth(OIDC)
   Dynamics[(Dynamics)]
   CAS[CAS]
   BCSC[BCSC]

   class Responders,Registrants,Suppliers,ESS,OAuth openshift_era
   class SSO openshift_util
   class BCSC,CAS,Dynamics bcgov

   Responders-->SSO;
   Responders-->ESS;
   Suppliers-->ESS;
   Registrants-->OAuth-->BCSC
   Registrants-->ESS;
   ESS-->Dynamics;
   ESS-->CAS;
```

## Components

| Directory                       | Role               |
| ------------------------------- | ------------------ |
| [ess](./ess/)                   | backend service    |
| [suppliers](./suppliers/)       | suppliers portal   |
| [registrants](./registrants/)   | registrants portal |
| [responders](./responders/)     | responders portal  |
| [landing-page](./landing-page/) | ESS landing page   |
| [oauth-server](./oauth-server/) | Oauth/OIDC service |
| [shared](./shared/)             | shared libraries   |

## Tests

| Directory                             | Role                                 |
| ------------------------------------- | ------------------------------------ |
| [automated-tests](./automated-tests/) | automated UI tests based on SpecFlow |
| [load-test](./load-test/)             | load test generator based on K9      |

## License

    Copyright 2022 Province of British Columbia

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at 

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
   