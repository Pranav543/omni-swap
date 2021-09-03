import smartpy as sp

# Import FA2 template
FA2 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")
# Define Cover_Token
class Cover_Token(FA2.FA2):
    pass


@sp.add_test(name="Fungible Token")
def test():
    scenario = sp.test_scenario()

    admin = sp.test_account("Decentralized Dictator")
    mark = sp.test_account("Mark")
    elon = sp.test_account("tesla")

    # Initialize Cover_Token as cover_token with single_asset = True
    cover_token = Cover_Token(
        FA2.FA2_config(single_asset=True, assume_consecutive_token_ids=False),
        admin=admin.address,
        metadata=sp.big_map(
            {
                "": sp.utils.bytes_of_string("tezos-storage:content"),
                "content": sp.utils.bytes_of_string("""{"name" : "Cover Token"}"""),
            }
        ),
    )
    scenario += cover_token
    # mint 5 tokens to mark
    scenario += cover_token.mint(
        address=mark.address,
        amount=5,
        metadata=Cover_Token.make_metadata(decimals=4, name="Cover Token", symbol="CB"),
        token_id=0,
    ).run(sender=admin)
    # mint 10 tokens to elon
    scenario += cover_token.mint(
        address=elon.address,
        amount=10,
        metadata=Cover_Token.make_metadata(decimals=4, name="Cover Token", symbol="CB"),
        token_id=0,
    ).run(sender=admin)

    # transfer 2 tokens from elon to mark.
    scenario += cover_token.transfer(
        [
            cover_token.batch_transfer.item(
                from_=elon.address,
                txs=[sp.record(amount=2, to_=mark.address, token_id=0)],
            )
        ]
    ).run(sender=elon)

    # create the FA2.View_consumer and add it to the scenario.
    consumer = FA2.View_consumer(cover_token)
    scenario += consumer
