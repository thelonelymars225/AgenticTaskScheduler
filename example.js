function greet(name) {
    return `Hello, ${name}!`;
}

const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);

console.log(greet("world"));
console.log("Doubled:", doubled);
