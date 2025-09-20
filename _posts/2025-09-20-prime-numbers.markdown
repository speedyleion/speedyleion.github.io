---
layout: post
title:  "Prime Number Brain Dump"
date:   2025-09-20 14:00:03 -0700
categories: math
---

<script type="text/javascript" async
  src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
</script>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true});</script>

I was watching an episode of Futurama titled "The Numberland Gap". In the
episode there was an interaction:
> Is it true that every even number is the addition of two primes?
> ...
> Can you prove it?[^1]

While Futurama is a meant be numerous cartoon, the writers happen to be very
knowledgable. So I thought perhaps this is a true theory that hasn't been
proven. This idea got the squirrel in my head spinning. 

I decided it would be interesting to capture what little I know of prime numbers
and pull on this idea some on my own. Perhaps afterward I could start to
look up some things and see if I gain any insight.

This post will be more or less a brain dump of what I know about primes and
pulling on the thread of the assumption that every even number is the addition
of two prime numbers.

# What Are Prime Numbers

My understanding of prime numbers is that they are whole numbers whose only
factors are themselves and one. Where _factors_ can only be whole numbers
themselves.[^2] 

Let's look at the first 6 integers:

| Number | Factors |
| -- | -- |
| 1 | 1 |
| 2 | 1, 2 |
| 3 | 1, 3 |
| 4 | 1, 2, 4 |
| 5 | 1, 5 |
| 6 | 1, 2, 3, 6 |

Focusing in on `6` we can see:

$$
\begin{align}
1 \times 6 &= 6 \\
2 \times 3 &= 6
\end{align}
$$

# Finding Primes

I recall in school we had a math exercise where we had 10x10 grid of all the
numbers from 1-100. The exercise went something like:
1. Starting at number one. 
2. Move to the next number that hasn't been marked off. This is $$n$$.
3. Step by $$n$$ and mark off the number you land on.
4. Repeat step $$3$$ until the end.
5. Go back to number $$n$$.
6. Repeat from step $$2$$, until $$n$$ is the last unmarked number.

<style>
.crossed-out {
  text-decoration: line-through;
  background-color: #ffebee;
  color: #999;
}
.cursor {
  background-color: #ffd54f;
  font-weight: bold;
  border: 2px solid #ff9800;
  padding: 2px 4px;
  border-radius: 3px;
}
</style>

We'll do an example looking at the first $$20$$ numbers. We start with all the
numbers unmarked.

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |

From number $$1$$ we move to the next number that hasn't been marked off, $$2$$.

| 1 | <span class="cursor">2</span> | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |

Now we step every $$2$$ and mark off those numbers. One may notice this is all
the even numbers.

| 1 | <span class="cursor">2</span> | 3 | <span class="crossed-out">4</span> | 5 | <span class="crossed-out">6</span> | 7 | <span class="crossed-out">8</span> | 9 | <span class="crossed-out">10</span> | 11 | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | 15 | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

We move to the next number that hasn't been marked off, $$3$$.

| 1 | 2 | <span class="cursor">3</span> | <span class="crossed-out">4</span> | 5 | <span class="crossed-out">6</span> | 7 | <span class="crossed-out">8</span> | 9 | <span class="crossed-out">10</span> | 11 | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | 15 | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

Now we step every $$3$$ and mark off those numbers. The numbers $$6$$, $$12$$, and
$$18$$ were already marked off, but it doesn't change the process.

| 1 | 2 | <span class="cursor">3</span> | <span class="crossed-out">4</span> | 5 | <span class="crossed-out">6</span> | 7 | <span class="crossed-out">8</span> | <span class="crossed-out">9</span> | <span class="crossed-out">10</span> | 11 | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | <span class="crossed-out">15</span> | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

We move to the next number that hasn't been marked off. This is $$5$$. This is
the first time we've moved past a marked off number.

| 1 | 2 | 3 | <span class="crossed-out">4</span> | <span class="cursor">5</span> | <span class="crossed-out">6</span> | 7 | <span class="crossed-out">8</span> | <span class="crossed-out">9</span> | <span class="crossed-out">10</span> | 11 | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | <span class="crossed-out">15</span> | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

Now we step every $$5$$ and mark off those numbers. All of these happened to be
marked off already.

| 1 | 2 | 3 | <span class="crossed-out">4</span> | <span class="cursor">5</span> | <span class="crossed-out">6</span> | 7 | <span class="crossed-out">8</span> | <span class="crossed-out">9</span> | <span class="crossed-out">10</span> | 11 | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | <span class="crossed-out">15</span> | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

We move to the next number that hasn't been marked off, $$7$$.

| 1 | 2 | 3 | <span class="crossed-out">4</span> | 5 | <span class="crossed-out">6</span> | <span class="cursor">7</span> | <span class="crossed-out">8</span> | <span class="crossed-out">9</span> | <span class="crossed-out">10</span> | 11 | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | <span class="crossed-out">15</span> | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

Now we step every $$7$$ and mark off those numbers. Again all of these happened
to be marked off already.

| 1 | 2 | 3 | <span class="crossed-out">4</span> | 5 | <span class="crossed-out">6</span> | <span class="cursor">7</span> | <span class="crossed-out">8</span> | <span class="crossed-out">9</span> | <span class="crossed-out">10</span> | 11 | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | <span class="crossed-out">15</span> | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

We move to the next number that hasn't been marked off, $$11$$. If we try to
step by $$11$$ we would go beyond the end of our max of $$20$$.

| 1 | 2 | 3 | <span class="crossed-out">4</span> | 5 | <span class="crossed-out">6</span> | 7 | <span class="crossed-out">8</span> | <span class="crossed-out">9</span> | <span class="crossed-out">10</span> | <span class="cursor">11</span> | <span class="crossed-out">12</span> | 13 | <span class="crossed-out">14</span> | <span class="crossed-out">15</span> | <span class="crossed-out">16</span> | 17 | <span class="crossed-out">18</span> | 19 | <span class="crossed-out">20</span> |

In the instructions I wrote:

> Step by $$n$$ and mark off the number you land on.

This is the same as saying mark off every number that is a multiple of $$n$$, that
isn't $$n$$. Thinking about it this way one can see that using this method to find
all primes in $$1, 2, 3, \ldots, x$$, a person only needs to do this up to
$$\frac{x}{2}$$. That's why above I stopped at $$11$$, because $$\frac{20}{2}=10$$

# Assuming Every Equal Number is the Sum of Two Primes

With my little understanding of prime numbers captured I wanted to start
thinking about the theory that every even number is the sum of two primes.

An even number is any number which is divisible by $$2$$. This means for any
prime number, $$p$$, we can take $$2p$$ and that will form an even number. We
can say that $$2p$$ is the sum of two primes, because $$2p = p + p$$.

With that in hand, my mind immediately went to the idea that the next even
number after $$2p$$ is $$\left(2p + 2\right)$$.  By replacing the multiplication
with addition and applying the associative property we can say the next even
number is $$\left(p + p + 2\right)$$.

$$
\begin{align}
2p + 2 &= \left(p + p\right) + 2 \\
       &= p + \left(p + 2\right)
\end{align}
$$

<div class="mermaid">
block
  columns 15
  a["2p + 2"]:15
  e["p"]:7 f["p + 2"]:8
</div>

We could take the simple assumption that $$\left(p+2\right)$$ is prime. Let's
see with the first few primes.

| $$p$$ | $$\left(p + 2\right)$$ |
| -- | -- |
| 1 | 3 |
| 2 | 4 |
| 3 | 5 |
| 5 | 7 |
| 7 | 9 |
| 11 | 13 |
| 13 | 15 |
| 17 | 19 |
| 19 | 21 |

Skipping over $$2$$, we don't get too far until we hit a prime number where
$$2$$ more isn't prime. This happens at $$7$$ where $$2$$ more is $$9$$ and
$$9$$ happens to have the factors $$1, 3, 9$$.

We do have some where $$p + 2$$ is prime. If we assume that all even numbers are
the sum of two primes then we should be able to say that there is at least one
prime number, $$q$$[^3], which is greater than $$p$$ and less than 
$$\left(2p + 2\right)$$.

$$
\{q : p < q < \left(2p+2\right)\}
$$

<div class="mermaid">
block
  columns 15
  a["2p + 2"]:15
  f["q"]:12 e["r"]:3 
</div>

At this point I realized I was making an assumption, that we knew all the prime
numbers up to $$p$$. In the diagram above, $$r$$ represents one of these
previously known prime numbers.

I was curious if we could simply try $$\left(2p + 2\right) = 1 + \left(2p + 1\right)$$.
$$1$$ is prime and $$\left(2p + 1\right)$$ is odd.

| $$p$$ | $$\left(2p + 1\right)$$ |
| -- | -- |
| 1 | 3 |
| 2 | 5 |
| 3 | 7 |
| 5 | 11 |
| 7 | 15 |
| 11 | 23 |
| 13 | 27 |
| 17 | 35 |
| 19 | 39 |

This simple approach fizzles out again at $$7$$. $$\left(2 \times 7\right) + 1 = 15$$ which has factors $$1, 3, 5, 15$$.

I was also curious if we could find a pattern in the occurrence of the primes.
If we look at how far a prime is from the next one, the _delta_ in the table can
we find any obvious patterns?

| prime | 1|    2 | 3 | 5 | 7 | 11| 13| 17| 19| 23| 29| 31| 37| 41| 43| 47| 53| 59| 61| 67| 71| 73| 79| 83| 89| 97 |
| delta | n/a | 1 | 1 | 2 | 2 | 4 | 2 | 4 | 2 | 4 | 6 | 2 | 6 | 4 | 2 | 4 | 6 | 6 | 2 | 6 | 4 | 2 | 6 | 4 | 6 | 8 |

It would likely require looking at quite a bit more primes past $$100$$ to be
able to reach a conclusion about if the delta between primes can provide
anything meaningful.

To be honest I'm a bit surprised the primes are that close together up to
$$100$$. I would have thought they would start to spread out faster and that
having primes $$2$$ apart wouldn't happen as often.

# Summary

This is about as far as I got with my limited knowledge. I know that large prime
numbers are used in things like RSA encryption. I also understand to generate an
RSA key pair requires one to search for two large primes and that there are
algorithms to search for primes. I don't know if these algorithms are based on
the theory that all even numbers are the sum of two primes. Is that even a
theory? 

I think I'll start to do some digging into primes and see what comes out of it.
Hopefully not too much is over my head so I can actually learn something.


# Footnotes:
[^1]: I don't recall the exact wording. As mentioned later in the post I wanted to keep off the internet lest I run across more information than I currently know on the topic of primes.

[^2]: I am not a mathematician so I'm sure there is a better definition, but again no looking things up for this post.
[^3]: I wouldn't be surprised if there are common letters used for prime numbers. If these aren't they, bear with me.


