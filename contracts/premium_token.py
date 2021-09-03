import smartpy as sp

# Import FA2 template
FA2 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")
# Define Premium_Token
class Premium_Token(FA2.FA2):
    pass


@sp.add_test(name="Fungible Token")
def test():
    scenario = sp.test_scenario()

    admin = sp.test_account("Decentralized Dictator")
    mark = sp.test_account("Mark")
    elon = sp.test_account("tesla")

    # Initialize Premium_Token as premium_token with single_asset = True
    premium_token = Premium_Token(
        FA2.FA2_config(single_asset=True, assume_consecutive_token_ids=False),
        admin=admin.address,
        metadata=sp.big_map(
            {
                "": sp.utils.bytes_of_string("tezos-storage:content"),
                "content": sp.utils.bytes_of_string("""{"name" : "Cover Token"}"""),
            }
        ),
    )
    scenario += premium_token
    # mint 5 tokens to mark
    scenario += premium_token.mint(
        address=mark.address,
        amount=5,
        metadata=Premium_Token.make_metadata(
            decimals=4, name="Premium Token", symbol="PT"
        ),
        token_id=0,
    ).run(sender=admin)
    # mint 10 tokens to elon
    scenario += premium_token.mint(
        address=elon.address,
        amount=10,
        metadata=Premium_Token.make_metadata(
            decimals=4, name="Premium Token", symbol="PT"
        ),
        token_id=0,
    ).run(sender=admin)

    # transfer 2 tokens from elon to mark.
    scenario += premium_token.transfer(
        [
            premium_token.batch_transfer.item(
                from_=elon.address,
                txs=[sp.record(amount=2, to_=mark.address, token_id=0)],
            )
        ]
    ).run(sender=elon)

    # create the FA2.View_consumer and add it to the scenario.
    consumer = FA2.View_consumer(premium_token)
    scenario += consumer
