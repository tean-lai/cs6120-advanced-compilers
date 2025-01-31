function bin_pow(x: bigint, n: bigint, acc: bigint): bigint {
  if (n === 0n) return acc;
  // if (n % 2n === 0n) return bin_pow(x * x, n / 2n, acc);
  // else return bin_pow(x, n - 1n, x * acc);
  return 0n;
}

console.log(bin_pow(2n, 10n, 1n));
console.log(bin_pow(3n, 5n, 1n));