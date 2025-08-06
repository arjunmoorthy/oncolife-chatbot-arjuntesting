import React from 'react';
import SimpleChatsPage from './pages/SimpleChatsPage';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>OncoLife Chatbot</h1>
      </header>
      <main>
        <SimpleChatsPage />
      </main>
    </div>
  );
}

export default App; 