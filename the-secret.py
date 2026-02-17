import os
THE_SECRET = os.environ['THE_SECRET']

gymweights = '  -=[|]=-  '
coded = []
midlength = int(0.5*len(THE_SECRET))

for c in THE_SECRET:
    coded.append(c)
    if len(coded) == midlength:
        coded.append(gymweights)
coded = ''.join(coded)
print()
print('The secret:\n')
print(coded)
print()
print(f"Remove the gymweights '{gymweights}' to get the secret")
print("Command suggestion (python):")
print(f"coded='{coded}'; gymweights='{gymweights}'; decoded=''.join(coded.split(gymweights)); print(decoded)")