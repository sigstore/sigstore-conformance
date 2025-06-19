## Paremetrized verification tests

Each subdirectory is used to parametrize test_verify():
* Name of the directory is the parametrized part of test name
* Name should end in "_fail" if the verification is expected to fail
* Directory must contain
  * `bundle.sigstore.json`: The signature bundle
  * `README`: Explanation of the test: why it should fail/succeed
* Directory may optionally contain
  * `artifact`: The signed artifact (if not provided, "a.txt" from the parent
    directory is used)
  * `trusted_root.json`: a custom trusted root (if one is not provided,
    the Sigstore public good production instance is used)
