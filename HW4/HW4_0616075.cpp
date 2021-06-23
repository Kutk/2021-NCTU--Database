#include <bits/stdc++.h>
using namespace std;
//N for sequential access
int maxn, N;


class Node{
    public:
    int sz = 0, szp = 0;
    int level;
    int key[22];
    bool leaf;
    int parPtrID;
    Node* ptr[22];
    Node* par;
    Node* sibling;

    //functions
    Node* create();
    void find(int);
    void print();
    void insert(int);
    void seq(int);
    void seq_print();
    void insertKey(int, int);
    void insertPtr(int, Node*);
    void split();
    void bfs();
};

Node* Node::create(){
    Node *cur = new Node;
    cur->sz = 0;
    cur->szp = 0;
    cur->leaf = 1;
    cur->par = NULL;
    cur->sibling = NULL;
    cur->parPtrID = -1;
    return cur;
}

void Node::find(int x){
    if(!sz && leaf && par == NULL){
        cout << "()" << endl << "QAQ" << endl << endl;
        return;
    }

    cout << "(";
    for(int i = 0; i < sz-1; i++)
        cout << key[i] << " ";
    cout << key[sz-1] << ")" <<endl;
    
    int p = sz - 1;
    while(p >= 0 && x < key[p])
        p--;
    //goto leaf to find x
    if(leaf){
        if(key[p] == x)
            cout << "Found" << endl << endl;
        else
            cout << "QAQ" << endl << endl;
    }else{
        p++;
        ptr[p]->find(x);
    }
}

void Node::insert(int x){
    int p = 0;
    //find place to insert
    while(p < sz){
        if(x < key[p]) break;
        p++;
    }

    if(leaf) 
        insertKey(p, x);
    else
        ptr[p]->insert(x);

    if(sz==maxn)
        split();
    
}

void Node::insertKey(int p, int x){
    //find place to insert key
    for(int i = sz-1; i >= p; i--)
        key[i+1] = key[i];
    key[p] = x;
    sz++;
}

void Node::insertPtr(int x, Node* p){
    for(int i = szp-1; i >= x; i--){
        ptr[i]->parPtrID++;
        ptr[i+1] = ptr[i];
    }
    ptr[x] = p;
    szp++;
}

void Node::split(){
    Node* splitnode = create();
    splitnode->leaf = leaf;
    if(sibling && leaf)
        splitnode->sibling = sibling;
    sibling = splitnode;

    //move key to new node
    while(sz > maxn/2){
        splitnode->key[splitnode->sz++] = key[sz-1];
        sz--;
    }

    //set ptr for new node
    while(szp > maxn/2+1){
        splitnode->ptr[splitnode->szp++] = ptr[szp-1];
        szp--;
    }

    reverse(splitnode->key, splitnode->key + splitnode->sz);
    reverse(splitnode->ptr, splitnode->ptr + splitnode->szp);

    for(int i = 0; i < splitnode->szp; i++){
        splitnode->ptr[i]->parPtrID = i;
        splitnode->ptr[i]->par = splitnode;
    }

    //create parent node
    if(!par){
        par = create();
        par->leaf = 0;
        parPtrID = 0;
        par->ptr[par->szp++] = this;
    }

    //set parent id for new node
    splitnode->par = par;
    splitnode->parPtrID = parPtrID+1;

    //link parent node to this node and splitnode
    par->insertKey(parPtrID, splitnode->key[0]);
    par->insertPtr(parPtrID+1, splitnode);
    if(!leaf){
        for(int i = 1; i < splitnode->sz; i++)
            splitnode->key[i-1] = splitnode->key[i];
        splitnode->sz--;
    }
}

void Node::print(){
    //for empty tree
    if(!sz && leaf && par == NULL){
        cout << "()" << endl;
        return;
    }
    //N level needs 2N space
    for(int i = 0; i < level*2; i++)
        cout << " ";
    cout << "(";
    for(int i = 0; i < sz-1; i++)
        cout << key[i] << " ";
    cout << key[sz-1] << ")" << endl;

    //pre-order traversal
    for(int i = 0; i < szp; i++){
        ptr[i]->print();
    }

}

void Node::bfs(){
    //set nodes level
    queue<Node*> q;
    q.push(this);
    while(!q.empty()){
        Node* cur = q.front();
        q.pop();
        if(cur -> par != NULL){
            cur->level = cur->par->level;
            cur->level++;
        }
        for(int i = 0; i < cur->szp; i++)
            q.push(cur->ptr[i]);
    }
}

void Node::seq(int x){   
    int p = sz - 1;
    while(p >= 0 && x < key[p])
        p--;
    //goto leaf to find x
    if(leaf){
        if(key[p] == x){
            for(int i = p; i < sz; i++){
                cout << key[i] << " ";
                N--;
                if(!N){
                    cout << endl << endl;
                    break;
                }
            }
            //test whether N is 0
            if(N && sibling != NULL)
                sibling->seq_print();
            else if(N && sibling == NULL)
                cout << endl << "N is too large" << endl << endl;
        }else
            cout << "Access Failed" << endl << endl;
    }else{
        p++;
        ptr[p]->seq(x);
    }
}

void Node::seq_print(){
    for(int i = 0; i < sz; i++){
        cout << key[i] << " ";
        N--;
        if(!N){
            cout << endl << endl;
            return;
        }
    }
    //test whether N is 0
    if(N && sibling == NULL)
        cout << endl << "N is too large" << endl << endl;
    else
        sibling->seq_print();
}

int main(){
    cin >> maxn;
    Node* bpt;
    bpt = bpt->create();
    while(1){
        string a;
        cin >> a;
        if(a == "i"){
            int x;
            cin >> x;
            bpt->insert(x);
            //move back to root
            while(bpt->par)
                bpt = bpt->par;
        }else if(a == "s"){
            int x;
            cin >> x;
            bpt->find(x);
            //move back to root
            while(bpt->par)
                bpt = bpt->par;
        }else if(a == "p"){
            bpt->level = 0;
            bpt->bfs();
            bpt->print();
            cout << endl;
        }else if(a == "a"){
            int x;
            cin >> x >> N;
            bpt->seq(x);
            //move back to root
            while(bpt->par)
                bpt = bpt->par;
        }else
            break;
    }
    return 0;
}