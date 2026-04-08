# useEffect Anti-Patterns

## 1. Redundant State for Derived Values

```tsx
// BAD: Extra state + Effect for derived value
function Form() {
  const [firstName, setFirstName] = useState('Taylor');
  const [lastName, setLastName] = useState('Swift');
  const [fullName, setFullName] = useState('');

  useEffect(() => {
    setFullName(firstName + ' ' + lastName);
  }, [firstName, lastName]);
}

// GOOD: Calculate during rendering
function Form() {
  const [firstName, setFirstName] = useState('Taylor');
  const [lastName, setLastName] = useState('Swift');
  const fullName = firstName + ' ' + lastName;
}
```

**Why it's bad**: Causes extra render pass with stale value, then re-renders with updated value.

---

## 2. Filtering/Transforming Data in Effect

```tsx
// BAD
function TodoList({ todos, filter }) {
  const [visibleTodos, setVisibleTodos] = useState([]);
  useEffect(() => {
    setVisibleTodos(getFilteredTodos(todos, filter));
  }, [todos, filter]);
}

// GOOD: Memoize if expensive
function TodoList({ todos, filter }) {
  const visibleTodos = useMemo(
    () => getFilteredTodos(todos, filter),
    [todos, filter]
  );
}
```

---

## 3. Resetting State on Prop Change

```tsx
// BAD
function ProfilePage({ userId }) {
  const [comment, setComment] = useState('');
  useEffect(() => { setComment(''); }, [userId]);
}

// GOOD: Use key prop
function ProfilePage({ userId }) {
  return <Profile userId={userId} key={userId} />;
}
function Profile({ userId }) {
  const [comment, setComment] = useState(''); // resets automatically
}
```

**Why key works**: React treats components with different keys as different instances, recreating state.

---

## 4. Event-Specific Logic in Effect

```tsx
// BAD: Effect fires on page refresh too
function ProductPage({ product, addToCart }) {
  useEffect(() => {
    if (product.isInCart) showNotification(`Added ${product.name}!`);
  }, [product]);

  function handleBuyClick() { addToCart(product); }
}

// GOOD: Handle in event handler
function ProductPage({ product, addToCart }) {
  function handleBuyClick() {
    addToCart(product);
    showNotification(`Added ${product.name}!`);
  }
}
```

---

## 5. Chains of Effects

```tsx
// BAD: Multiple Effects triggering each other = multiple re-renders
useEffect(() => { if (card?.gold) setGoldCardCount(c => c + 1); }, [card]);
useEffect(() => { if (goldCardCount > 3) { setRound(r => r + 1); setGoldCardCount(0); } }, [goldCardCount]);
useEffect(() => { if (round > 5) setIsGameOver(true); }, [round]);

// GOOD: Calculate in event handler
function handlePlaceCard(nextCard) {
  setCard(nextCard);
  if (nextCard.gold) {
    if (goldCardCount < 3) { setGoldCardCount(goldCardCount + 1); }
    else { setGoldCardCount(0); setRound(round + 1); }
  }
}
```

---

## 6. Notifying Parent via Effect

```tsx
// BAD
function Toggle({ onChange }) {
  const [isOn, setIsOn] = useState(false);
  useEffect(() => { onChange(isOn); }, [isOn, onChange]);
  function handleClick() { setIsOn(!isOn); }
}

// GOOD: Notify in same event
function Toggle({ onChange }) {
  const [isOn, setIsOn] = useState(false);
  function updateToggle(nextIsOn) {
    setIsOn(nextIsOn);
    onChange(nextIsOn); // same event, batched render
  }
  function handleClick() { updateToggle(!isOn); }
}
```

---

## 7. Passing Data Up to Parent

```tsx
// BAD: Child fetches, passes up via Effect
function Child({ onFetched }) {
  const data = useSomeAPI();
  useEffect(() => { if (data) onFetched(data); }, [onFetched, data]);
}

// GOOD: Parent fetches, passes down
function Parent() {
  const data = useSomeAPI();
  return <Child data={data} />;
}
```

---

## 8. Fetching Without Cleanup (Race Condition)

```tsx
// BAD: "hello" response may arrive after "hell"
useEffect(() => {
  fetchResults(query).then(json => setResults(json));
}, [query]);

// GOOD: Cleanup ignores stale responses
useEffect(() => {
  let ignore = false;
  fetchResults(query).then(json => { if (!ignore) setResults(json); });
  return () => { ignore = true; };
}, [query]);
```

---

## 9. App Initialization in Effect

```tsx
// BAD: Runs twice in dev, may break auth
function App() {
  useEffect(() => { checkAuthToken(); }, []);
}

// GOOD: Module-level guard
let didInit = false;
function App() {
  useEffect(() => {
    if (!didInit) { didInit = true; checkAuthToken(); }
  }, []);
}
```
