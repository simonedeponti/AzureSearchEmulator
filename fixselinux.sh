#!/bin/bash

sudo chcon -R -u system_u -t svirt_sandbox_file_t -l s0 AzureSearchEmulator