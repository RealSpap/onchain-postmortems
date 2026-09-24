#!/usr/bin/env python3
"""
Recovers the signer of the conversionIn signature used in tx
0xfe12c63b322d52727c615f3342222138d1563400a9880cebb516a9a162ac69e2
and compares it with the converter's own stored conversionAuthorizer.

This is the check that decides whether the signature was FORGED (recovery
would not match any authorized signer) or VALID and produced by the real
authorizer key (recovery matches the stored address exactly).

Needs eth_hash and eth_keys.
"""
from eth_hash.auto import keccak
from eth_keys.datatypes import Signature

# calldata words of the conversionIn call, read straight off the tx
to     = bytes.fromhex('2dcc1085fdcf418b421e45e86e4e54637cc21dfe')
amount = (0x736db1c45ee48b7cc9c00).to_bytes(32, 'big')
cid    = bytes.fromhex('bf294b48886f1868ff0ce030edbf1f4cba4771db4a58eef42ce652f3b080aa71')
this   = bytes.fromhex('ab424a430cc09864fa1277a38193111705adf3a3')  # the converter
sender = bytes.fromhex('1572f2af7696b39c85e3221cde8efb640f86c362')  # msg.sender

v = 28
r = bytes.fromhex('83f99d754d5d6f3a903ad8572f6bc7a9fda73249b3e7181d5710afc30eab0a12')
s = bytes.fromhex('365b484204e9172b666e9e97733baf2f02bd9782826291f29f8939c25bbab7ba')
sig = Signature(vrs=(v - 27, int.from_bytes(r, 'big'), int.from_bytes(s, 'big')))

# the message the contract hashes, recovered by exhaustive search over the
# plausible abi.encodePacked orderings (only this one recovers to the
# stored authorizer, so this is the encoding the contract uses):
#   keccak256("__conversionIn", amount, msg.sender, conversionId, address(this))
# then wrapped in the EIP-191 personal_sign prefix.
inner = keccak(b'__conversionIn' + amount + sender + cid + this)
digest = keccak(b'\x19Ethereum Signed Message:\n32' + inner)
recovered = sig.recover_public_key_from_msg_hash(digest).to_checksum_address()

STORED_AUTHORIZER = '0x69e5446b07b23de0a76730062c3252152216c85c'
print('inner hash          :', '0x' + inner.hex())
print('personal_sign digest:', '0x' + digest.hex())
print('recovered signer    :', recovered)
print('stored authorizer   :', STORED_AUTHORIZER)
print()
match = recovered.lower() == STORED_AUTHORIZER
print('MATCH:', match)
print()
print('Conclusion: the signature is %s.' % (
    'VALID and was produced by the contract\'s own conversion authorizer key'
    if match else 'NOT from the stored authorizer'))
