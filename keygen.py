"""강사 열쇠 만들기. 한 번만 실행합니다.

출력되는 publicKey 는 config.json 에 넣고(공개되어도 괜찮음),
강사 링크(#teach. 뒤의 글자)는 강사만 갖고 있습니다. 이 링크가 있어야 진행 위치를 보낼 수 있습니다.
"""
import base64, json
from cryptography.hazmat.primitives.asymmetric import ec

def b64u(n: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes(32, 'big')).rstrip(b'=').decode()

k = ec.generate_private_key(ec.SECP256R1())
pub = k.public_key().public_numbers()
jwk = {'kty': 'EC', 'crv': 'P-256', 'x': b64u(pub.x), 'y': b64u(pub.y), 'ext': True}
print('config.json 의 "publicKey" 에 넣을 값:')
print(json.dumps(jwk))
print()
print('강사 링크 끝에 붙일 부분 (아무에게도 보내지 마세요):')
print('#teach.' + b64u(k.private_numbers().private_value))
